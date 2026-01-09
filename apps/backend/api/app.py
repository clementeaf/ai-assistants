from __future__ import annotations

import os
import uuid
from collections.abc import Awaitable, Callable
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars, get_contextvars

from ai_assistants.api.models import (
    BaileysInboundResponse,
    BaileysInboundRequest,
    CreateJobResponse,
    CustomerMemoryResponse,
    JobStatusResponse,
    SendMessageRequest,
    SendMessageResponse,
    WhatsAppGatewayInboundRequest,
    WhatsAppGatewayInboundResponse,
    WhatsAppInboundRequest,
    WebSocketMessage,
)
from ai_assistants.channels.models import Channel, InboundMessage
from ai_assistants.channels.webhook_security import load_webhook_security_config, verify_signature
from ai_assistants.observability.logging import configure_logging
from ai_assistants.orchestrator.runtime import Orchestrator
from ai_assistants.persistence.sqlite_store import SqliteConversationStore, load_sqlite_store_config
from ai_assistants.persistence.sqlite_job_store import SqliteJobStore, load_sqlite_job_store_config
from ai_assistants.persistence.sqlite_memory_store import SqliteCustomerMemoryStore, load_sqlite_memory_store_config
from ai_assistants.config.cors_config import CORSConfig, load_cors_config
from ai_assistants.security.auth import AuthContext, require_auth, parse_api_keys, is_auth_enabled
from ai_assistants.security.rate_limit import InMemoryRateLimiter, load_rate_limit_config
from ai_assistants.jobs.callbacks import JobCallbackSender, load_job_callback_config

configure_logging()


def _is_legacy_routes_enabled() -> bool:
    """Return true if legacy (non-/v1) routes are enabled."""
    raw = os.getenv("AI_ASSISTANTS_ENABLE_LEGACY_ROUTES", "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def create_app() -> FastAPI:
    """Create the FastAPI application with conditional legacy route registration."""
    executor = ThreadPoolExecutor(max_workers=4)

    @asynccontextmanager
    async def _lifespan(_app: FastAPI):
        yield
        executor.shutdown(wait=False, cancel_futures=True)

    app = FastAPI(title="AI Assistants API", version="0.1.0", lifespan=_lifespan)

    cors_config = load_cors_config()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_config.allowed_origins,
        allow_credentials=cors_config.allow_credentials,
        allow_methods=cors_config.allowed_methods,
        allow_headers=cors_config.allowed_headers,
        expose_headers=cors_config.exposed_headers,
        max_age=cors_config.max_age,
    )

    @app.middleware("http")
    async def request_context_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Middleware to add request context and request ID to logs."""
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        bind_contextvars(
            request_id=request_id,
            http_method=request.method,
            http_path=request.url.path,
        )
        try:
            response = await call_next(request)
        finally:
            clear_contextvars()
        response.headers["X-Request-Id"] = request_id
        return response

    store = SqliteConversationStore(load_sqlite_store_config())
    job_store = SqliteJobStore(load_sqlite_job_store_config())
    memory_store = SqliteCustomerMemoryStore(load_sqlite_memory_store_config())
    orchestrator = Orchestrator(store=store, memory_store=memory_store)
    rate_limit_config = load_rate_limit_config()
    rate_limiter = InMemoryRateLimiter(rate_limit_config) if rate_limit_config is not None else None
    callback_cfg = load_job_callback_config()
    callback_sender = JobCallbackSender(callback_cfg) if callback_cfg is not None else None

    def _enforce_rate_limit(auth: AuthContext) -> None:
        """Enforce rate limit if enabled."""
        if rate_limiter is None:
            return
        rate_limiter.check(key=auth.project_id)

    def _bind_auth_context(auth: AuthContext) -> None:
        """Bind auth-derived fields to the current request context."""
        bind_contextvars(project_id=auth.project_id)

    def _run_turn(conversation_id: str, text: str) -> SendMessageResponse:
        """Run a conversation turn and return the standard response envelope."""
        result = orchestrator.run_turn(conversation_id=conversation_id, user_text=text)
        return SendMessageResponse(conversation_id=result.conversation_id, response_text=result.response_text)

    def _run_turn_with_customer(
        *, conversation_id: str, text: str, customer_id: str | None
    ) -> SendMessageResponse:
        """Run a conversation turn with optional customer identity."""
        result = orchestrator.run_turn(
            conversation_id=conversation_id,
            user_text=text,
            customer_id=customer_id,
        )
        return SendMessageResponse(conversation_id=result.conversation_id, response_text=result.response_text)

    async def _handle_whatsapp_gateway_inbound(
        request: Request,
        payload: WhatsAppGatewayInboundRequest,
        x_webhook_timestamp: str | None = Header(default=None),
        x_webhook_signature: str | None = Header(default=None),
    ) -> WhatsAppGatewayInboundResponse:
        """Common handler for WhatsApp gateway inbound payloads.

        Security: if WHATSAPP_WEBHOOK_SECRET is configured, this endpoint expects:
        - X-Webhook-Timestamp: unix epoch seconds (string)
        - X-Webhook-Signature: base64(HMAC_SHA256(secret, timestamp + "." + raw_body))
        """
        config = load_webhook_security_config()
        if config is not None:
            if x_webhook_timestamp is None or x_webhook_signature is None:
                raise HTTPException(status_code=401, detail="Missing webhook signature headers")
            body_bytes = await request.body()
            if not verify_signature(
                config=config, timestamp=x_webhook_timestamp, signature=x_webhook_signature, body_bytes=body_bytes
            ):
                raise HTTPException(status_code=401, detail="Invalid webhook signature")

        inbound = InboundMessage(channel=Channel.whatsapp, sender_id=payload.from_number, text=payload.text)
        customer_id = payload.customer_id or payload.from_number
        
        # Si viene customer_name de WhatsApp, cargar la conversación y actualizar el nombre
        # antes de procesarla (si aún no tiene nombre)
        conversation_id = inbound.conversation_id()
        existing_conv = store.get(conversation_id)
        if payload.customer_name and (existing_conv is None or existing_conv.customer_name is None):
            # Crear o actualizar la conversación con el nombre de WhatsApp
            if existing_conv is None:
                from ai_assistants.orchestrator.state import ConversationState
                existing_conv = ConversationState(
                    conversation_id=conversation_id,
                    customer_id=customer_id,
                    customer_name=payload.customer_name,
                )
                store.put(existing_conv)
            else:
                updated_conv = existing_conv.model_copy(update={"customer_name": payload.customer_name})
                store.put(updated_conv)
        
        result = orchestrator.run_turn(
            conversation_id=conversation_id,
            user_text=inbound.text,
            event_id=payload.message_id,
            customer_id=customer_id,
        )
        return WhatsAppGatewayInboundResponse(
            conversation_id=result.conversation_id,
            message_id=payload.message_id,
            response_text=result.response_text,
            interactive_type=result.interactive_type,
            buttons=result.buttons,
            list_title=result.list_title,
            list_items=result.list_items,
        )

    def _schedule_turn_job(
        *, conversation_id: str, user_text: str, customer_id: str | None, message_id: str | None
    ) -> str:
        job_id = str(uuid.uuid4())
        job_store.create(job_id=job_id, conversation_id=conversation_id, message_id=message_id)
        captured_context = dict(get_contextvars())

        def _run() -> None:
            if len(captured_context) > 0:
                bind_contextvars(**captured_context)
            job_store.mark_running(job_id)
            try:
                result = orchestrator.run_turn(
                    conversation_id=conversation_id,
                    user_text=user_text,
                    event_id=message_id,
                    customer_id=customer_id,
                )
                job_store.mark_succeeded(job_id, result.response_text)
                if callback_sender is not None:
                    record = job_store.get(job_id)
                    if record is not None:
                        callback_sender.notify(record)
            except Exception as exc:  # noqa: BLE001
                job_store.mark_failed(job_id, str(exc))
                if callback_sender is not None:
                    record = job_store.get(job_id)
                    if record is not None:
                        callback_sender.notify(record)
            finally:
                clear_contextvars()

        executor.submit(_run)
        return job_id

    v1 = APIRouter(prefix="/v1")
    legacy = APIRouter()

    async def _authenticate_websocket(api_key: str | None) -> AuthContext | None:
        """Authenticate WebSocket connection using API key from query params."""
        if not is_auth_enabled():
            bind_contextvars(project_id="dev")
            return AuthContext(project_id="dev", api_key="dev")

        if api_key is None or api_key.strip() == "":
            return None

        raw = os.getenv("AI_ASSISTANTS_API_KEYS", "")
        mapping = parse_api_keys(raw)
        for project_id, expected_key in mapping.items():
            if api_key == expected_key:
                bind_contextvars(project_id=project_id)
                return AuthContext(project_id=project_id, api_key=api_key)

        return None

    @v1.websocket("/ws/conversations/{conversation_id}")
    async def websocket_chat(
        websocket: WebSocket,
        conversation_id: str,
    ):
        """WebSocket endpoint for real-time chat with AI assistant.
        
        Establishes a persistent WebSocket connection for bidirectional communication.
        Supports ping/pong for connection health checks.
        
        Query Parameters:
            api_key: API key for authentication (required if auth enabled)
            customer_id: Optional customer ID for personalization
            
        Message Types:
            - user_message: Client sends user message with text field
            - assistant_message: Server sends AI response with text field
            - ping: Client sends ping, server responds with pong
            - pong: Server response to ping
            - error: Server sends error information
            
        Example:
            ```javascript
            const ws = new WebSocket('ws://localhost:8000/v1/ws/conversations/test?api_key=key&customer_id=123');
            ws.send(JSON.stringify({type: 'user_message', text: 'Hola'}));
            ```
        """
        # Aceptar conexión primero (requerido por FastAPI)
        await websocket.accept()
        
        # Obtener query params de la URL
        query_params = dict(websocket.query_params)
        api_key = query_params.get("api_key")
        customer_id = query_params.get("customer_id")
        
        # Autenticar después de aceptar
        auth = await _authenticate_websocket(api_key)
        
        if auth is None and is_auth_enabled():
            error_msg = WebSocketMessage(
                type="error",
                conversation_id=conversation_id,
                error="Authentication failed: Invalid or missing API key",
            )
            await websocket.send_json(error_msg.model_dump())
            await websocket.close(code=1008, reason="Authentication failed")
            return

        try:
            if auth is None:
                auth = AuthContext(project_id="dev", api_key="dev")
            _bind_auth_context(auth)

            request_id = str(uuid.uuid4())
            bind_contextvars(
                request_id=request_id,
                http_method="WS",
                http_path=f"/v1/ws/conversations/{conversation_id}",
            )

            while True:
                try:
                    data = await websocket.receive_json()
                    message = WebSocketMessage.model_validate(data)

                    if message.type == "ping":
                        await websocket.send_json(
                            WebSocketMessage(type="pong", conversation_id=conversation_id).model_dump()
                        )
                        continue

                    if message.type != "user_message" or message.text is None:
                        await websocket.send_json(
                            WebSocketMessage(
                                type="error",
                                conversation_id=conversation_id,
                                error="Invalid message type or missing text",
                            ).model_dump()
                        )
                        continue

                    if rate_limiter is not None:
                        try:
                            rate_limiter.check(key=auth.project_id)
                        except HTTPException:
                            await websocket.send_json(
                                WebSocketMessage(
                                    type="error",
                                    conversation_id=conversation_id,
                                    error="Rate limit exceeded",
                                ).model_dump()
                            )
                            continue

                    result = orchestrator.run_turn(
                        conversation_id=conversation_id,
                        user_text=message.text,
                        customer_id=customer_id,
                    )

                    from datetime import datetime

                    response = WebSocketMessage(
                        type="assistant_message",
                        text=result.response_text,
                        conversation_id=result.conversation_id,
                        timestamp=datetime.utcnow().isoformat() + "Z",
                    )

                    await websocket.send_json(response.model_dump())

                except WebSocketDisconnect:
                    break
                except Exception as exc:  # noqa: BLE001
                    from datetime import datetime

                    error_msg = WebSocketMessage(
                        type="error",
                        conversation_id=conversation_id,
                        error=str(exc),
                        timestamp=datetime.utcnow().isoformat() + "Z",
                    )
                    await websocket.send_json(error_msg.model_dump())

        except WebSocketDisconnect:
            pass
        except Exception as exc:  # noqa: BLE001
            try:
                error_msg = WebSocketMessage(
                    type="error",
                    conversation_id=conversation_id,
                    error=f"Internal error: {str(exc)}",
                )
                await websocket.send_json(error_msg.model_dump())
                await websocket.close(code=1011, reason=f"Internal error: {str(exc)}")
            except Exception:  # noqa: BLE001
                pass
        finally:
            clear_contextvars()

    @v1.post("/conversations/{conversation_id}/messages", response_model=SendMessageResponse)
    def v1_send_message(
        conversation_id: str,
        payload: SendMessageRequest,
        auth: AuthContext = Depends(require_auth),
        x_customer_id: str | None = Header(default=None),
    ) -> SendMessageResponse:
        """Run a conversation turn for the given conversation id.
        
        Args:
            conversation_id: Unique identifier for the conversation
            payload: Request body containing the user message text
            auth: Authentication context (injected via dependency)
            x_customer_id: Optional customer ID header for personalization
            
        Returns:
            SendMessageResponse with conversation_id and response_text
            
        Example:
            ```python
            POST /v1/conversations/whatsapp:+1234567890/messages
            {
                "text": "Quiero hacer una reserva"
            }
            ```
        """
        _bind_auth_context(auth)
        _enforce_rate_limit(auth)
        return _run_turn_with_customer(conversation_id=conversation_id, text=payload.text, customer_id=x_customer_id)

    @v1.post("/channels/web/conversations/{conversation_id}/messages", response_model=SendMessageResponse)
    def v1_web_send_message(
        conversation_id: str,
        payload: SendMessageRequest,
        auth: AuthContext = Depends(require_auth),
        x_customer_id: str | None = Header(default=None),
    ) -> SendMessageResponse:
        """Web channel alias for sending a message into a conversation."""
        _bind_auth_context(auth)
        _enforce_rate_limit(auth)
        return _run_turn_with_customer(conversation_id=conversation_id, text=payload.text, customer_id=x_customer_id)

    @v1.post("/async/conversations/{conversation_id}/messages", status_code=202, response_model=CreateJobResponse)
    def v1_async_send_message(
        conversation_id: str,
        payload: SendMessageRequest,
        auth: AuthContext = Depends(require_auth),
        x_customer_id: str | None = Header(default=None),
    ) -> CreateJobResponse:
        """Schedule an async conversation turn and return a job id.
        
        This endpoint schedules the conversation turn to be processed asynchronously
        and immediately returns a job ID. Use the job ID to check status via
        GET /v1/jobs/{job_id}.
        
        Args:
            conversation_id: Unique identifier for the conversation
            payload: Request body containing the user message text
            auth: Authentication context (injected via dependency)
            x_customer_id: Optional customer ID header for personalization
            
        Returns:
            CreateJobResponse with job_id to track the async operation
            
        Example:
            ```python
            POST /v1/async/conversations/whatsapp:+1234567890/messages
            {
                "text": "Quiero hacer una reserva"
            }
            # Returns: {"job_id": "abc-123-def"}
            ```
        """
        _bind_auth_context(auth)
        _enforce_rate_limit(auth)
        job_id = _schedule_turn_job(
            conversation_id=conversation_id,
            user_text=payload.text,
            customer_id=x_customer_id,
            message_id=None,
        )
        return CreateJobResponse(job_id=job_id)

    @v1.post("/async/channels/whatsapp/gateway/inbound", status_code=202, response_model=CreateJobResponse)
    async def v1_async_whatsapp_gateway_inbound(
        request: Request,
        payload: WhatsAppGatewayInboundRequest,
        x_webhook_timestamp: str | None = Header(default=None),
        x_webhook_signature: str | None = Header(default=None),
        auth: AuthContext = Depends(require_auth),
    ) -> CreateJobResponse:
        """Schedule async processing for WhatsApp gateway inbound (for slow hooks/flows)."""
        _bind_auth_context(auth)
        _enforce_rate_limit(auth)
        # validate webhook if enabled (reuse handler logic) but do not run the turn inline
        config = load_webhook_security_config()
        if config is not None:
            if x_webhook_timestamp is None or x_webhook_signature is None:
                raise HTTPException(status_code=401, detail="Missing webhook signature headers")
            body_bytes = await request.body()
            if not verify_signature(
                config=config, timestamp=x_webhook_timestamp, signature=x_webhook_signature, body_bytes=body_bytes
            ):
                raise HTTPException(status_code=401, detail="Invalid webhook signature")

        conversation_id = f"whatsapp:{payload.from_number}"
        customer_id = payload.customer_id or payload.from_number
        job_id = _schedule_turn_job(
            conversation_id=conversation_id,
            user_text=payload.text,
            customer_id=customer_id,
            message_id=payload.message_id,
        )
        return CreateJobResponse(job_id=job_id)

    @v1.get("/jobs/{job_id}", response_model=JobStatusResponse)
    def v1_get_job(job_id: str, auth: AuthContext = Depends(require_auth)) -> JobStatusResponse:
        """Fetch async job status/result.
        
        Args:
            job_id: The job ID returned from an async endpoint
            auth: Authentication context (injected via dependency)
            
        Returns:
            JobStatusResponse with status, result, or error information
            
        Status values:
            - "pending": Job is queued but not started
            - "running": Job is currently being processed
            - "succeeded": Job completed successfully (response_text available)
            - "failed": Job failed (error_text available)
        """
        _bind_auth_context(auth)
        _enforce_rate_limit(auth)
        record = job_store.get(job_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return JobStatusResponse(
            job_id=record.job_id,
            status=record.status.value,
            conversation_id=record.conversation_id,
            message_id=record.message_id,
            response_text=record.response_text,
            error_text=record.error_text,
        )

    @v1.get("/memory", response_model=CustomerMemoryResponse)
    def v1_get_memory(
        auth: AuthContext = Depends(require_auth),
        x_customer_id: str | None = Header(default=None),
    ) -> CustomerMemoryResponse:
        """Get long-term memory for a customer.
        
        Retrieves persistent memory data associated with a customer, including
        last order IDs, tracking IDs, and other customer-specific information.
        
        Args:
            auth: Authentication context (injected via dependency)
            x_customer_id: Customer ID header (required)
            
        Returns:
            CustomerMemoryResponse with customer_id and memory dictionary
            
        Raises:
            HTTPException 400: If X-Customer-Id header is missing
        """
        _bind_auth_context(auth)
        _enforce_rate_limit(auth)
        if x_customer_id is None or x_customer_id.strip() == "":
            raise HTTPException(status_code=400, detail="Missing X-Customer-Id")
        mem = memory_store.get(project_id=auth.project_id, customer_id=x_customer_id)
        return CustomerMemoryResponse(customer_id=x_customer_id, memory=mem.data if mem else {})

    @v1.delete("/memory", status_code=204)
    def v1_delete_memory(
        auth: AuthContext = Depends(require_auth),
        x_customer_id: str | None = Header(default=None),
    ) -> None:
        """Delete long-term memory for a customer (forget)."""
        _bind_auth_context(auth)
        _enforce_rate_limit(auth)
        if x_customer_id is None or x_customer_id.strip() == "":
            raise HTTPException(status_code=400, detail="Missing X-Customer-Id")
        memory_store.delete(project_id=auth.project_id, customer_id=x_customer_id)
        return None

    @v1.post("/channels/whatsapp/inbound", response_model=SendMessageResponse)
    def v1_whatsapp_inbound(
        payload: WhatsAppInboundRequest, auth: AuthContext = Depends(require_auth)
    ) -> SendMessageResponse:
        """WhatsApp inbound endpoint using a stable internal message contract."""
        _bind_auth_context(auth)
        _enforce_rate_limit(auth)
        inbound = InboundMessage(channel=Channel.whatsapp, sender_id=payload.from_number, text=payload.text)
        return _run_turn(conversation_id=inbound.conversation_id(), text=inbound.text)

    @v1.post("/channels/whatsapp/gateway/inbound", response_model=WhatsAppGatewayInboundResponse)
    async def v1_whatsapp_gateway_inbound(
        request: Request,
        payload: WhatsAppGatewayInboundRequest,
        x_webhook_timestamp: str | None = Header(default=None),
        x_webhook_signature: str | None = Header(default=None),
        auth: AuthContext = Depends(require_auth),
    ) -> WhatsAppGatewayInboundResponse:
        """Universal WhatsApp inbound endpoint for any gateway service."""
        _bind_auth_context(auth)
        _enforce_rate_limit(auth)
        return await _handle_whatsapp_gateway_inbound(
            request=request,
            payload=payload,
            x_webhook_timestamp=x_webhook_timestamp,
            x_webhook_signature=x_webhook_signature,
        )

    @legacy.post("/conversations/{conversation_id}/messages", response_model=SendMessageResponse)
    def send_message(conversation_id: str, payload: SendMessageRequest) -> SendMessageResponse:
        """Run a conversation turn for the given conversation id (legacy)."""
        return _run_turn(conversation_id=conversation_id, text=payload.text)

    @legacy.post("/channels/web/conversations/{conversation_id}/messages", response_model=SendMessageResponse)
    def web_send_message(conversation_id: str, payload: SendMessageRequest) -> SendMessageResponse:
        """Web channel alias for sending a message into a conversation (legacy)."""
        return _run_turn(conversation_id=conversation_id, text=payload.text)

    @legacy.post("/channels/whatsapp/inbound", response_model=SendMessageResponse)
    def whatsapp_inbound(payload: WhatsAppInboundRequest) -> SendMessageResponse:
        """WhatsApp inbound endpoint using a stable internal message contract (legacy)."""
        inbound = InboundMessage(channel=Channel.whatsapp, sender_id=payload.from_number, text=payload.text)
        return _run_turn(conversation_id=inbound.conversation_id(), text=inbound.text)

    @legacy.post("/channels/whatsapp/gateway/inbound", response_model=WhatsAppGatewayInboundResponse)
    async def whatsapp_gateway_inbound(
        request: Request,
        payload: WhatsAppGatewayInboundRequest,
        x_webhook_timestamp: str | None = Header(default=None),
        x_webhook_signature: str | None = Header(default=None),
    ) -> WhatsAppGatewayInboundResponse:
        """Universal WhatsApp inbound endpoint for any gateway service (legacy)."""
        return await _handle_whatsapp_gateway_inbound(
            request=request,
            payload=payload,
            x_webhook_timestamp=x_webhook_timestamp,
            x_webhook_signature=x_webhook_signature,
        )

    @legacy.post("/channels/whatsapp/baileys/inbound", response_model=BaileysInboundResponse)
    async def whatsapp_baileys_inbound(
        request: Request,
        payload: BaileysInboundRequest,
        x_webhook_timestamp: str | None = Header(default=None),
        x_webhook_signature: str | None = Header(default=None),
    ) -> BaileysInboundResponse:
        """Backward-compatible alias for Baileys-based gateways."""
        result = await _handle_whatsapp_gateway_inbound(
            request=request,
            payload=WhatsAppGatewayInboundRequest(
                message_id=payload.message_id,
                from_number=payload.from_number,
                text=payload.text,
                timestamp_iso=payload.timestamp_iso,
            ),
            x_webhook_timestamp=x_webhook_timestamp,
            x_webhook_signature=x_webhook_signature,
        )
        return BaileysInboundResponse(
            conversation_id=result.conversation_id,
            message_id=result.message_id,
            response_text=result.response_text,
        )

    app.include_router(v1)
    if _is_legacy_routes_enabled():
        app.include_router(legacy)

    return app


app = create_app()


