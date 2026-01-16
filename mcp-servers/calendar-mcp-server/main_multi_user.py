#!/usr/bin/env python3
"""MCP Calendar Server - Multi-user Google Calendar support."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

# Cargar variables de entorno desde .env
load_dotenv()

from backends import SQLiteBackend
from oauth2_handler import OAuth2Handler
from token_store import TokenStore

try:
    from backends import GoogleCalendarBackend
except ImportError:
    GoogleCalendarBackend = None

app = FastAPI(title="MCP Calendar Server", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)


class MCPRequest(BaseModel):
    """MCP JSON-RPC request."""

    jsonrpc: str = "2.0"
    id: int | str
    method: str
    params: dict


class MCPResponse(BaseModel):
    """MCP JSON-RPC response."""

    jsonrpc: str = "2.0"
    id: int | str
    result: dict | None = None
    error: dict | None = None


class OAuthAuthorizeRequest(BaseModel):
    """Request to start OAuth2 flow."""

    customer_id: str


class OAuthDisconnectRequest(BaseModel):
    """Request to disconnect Google Calendar."""

    customer_id: str


backend = None
oauth2_handler = None
token_store = None


def get_backend():
    """
    Get the configured calendar backend.
    @returns CalendarBackend instance
    """
    global oauth2_handler, token_store
    
    backend_type = os.getenv("CALENDAR_BACKEND", "sqlite").lower()

    if backend_type == "google_calendar":
        if GoogleCalendarBackend is None:
            raise ValueError(
                "Google Calendar backend not available. Install google-api-python-client and google-auth-httplib2"
            )

        client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
        redirect_uri = os.getenv("GOOGLE_OAUTH_REDIRECT_URI")
        token_db_path = Path(os.getenv("TOKEN_DB_PATH", "tokens.db"))
        encryption_key = os.getenv("TOKEN_ENCRYPTION_KEY")

        if client_id and client_secret and redirect_uri:
            token_store = TokenStore(db_path=token_db_path, encryption_key=encryption_key)
            oauth2_handler = OAuth2Handler(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                token_store=token_store,
            )
            return GoogleCalendarBackend(oauth2_handler=oauth2_handler)
        else:
            service_account_file = os.getenv("GOOGLE_CALENDAR_SERVICE_ACCOUNT_FILE")
            calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")
            return GoogleCalendarBackend(
                service_account_file=service_account_file,
                calendar_id=calendar_id,
            )
    else:
        db_path = Path(os.getenv("CALENDAR_DB_PATH", "calendar.db"))
        return SQLiteBackend(db_path=db_path)


@app.on_event("startup")
def startup_event():
    """Initialize backend on startup."""
    global backend, oauth2_handler, token_store
    try:
        backend = get_backend()
        # Asegurar que oauth2_handler y token_store estén disponibles globalmente
        # (get_backend() los inicializa, pero necesitamos asegurarnos de que estén disponibles)
        print(f"[STARTUP] Backend initialized: {type(backend).__name__}")
        if oauth2_handler:
            print(f"[STARTUP] OAuth2 handler initialized")
        if token_store:
            print(f"[STARTUP] Token store initialized")
    except Exception as e:
        print(f"Error initializing backend: {e}")
        raise


@app.post("/oauth/authorize")
async def oauth_authorize(request: OAuthAuthorizeRequest):
    """
    Start OAuth2 authorization flow for a customer.
    @param request - Request with customer_id
    @returns Authorization URL and state
    """
    global oauth2_handler
    if oauth2_handler is None:
        raise HTTPException(status_code=400, detail="OAuth2 not configured")

    try:
        result = oauth2_handler.get_authorization_url(request.customer_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/oauth/callback")
async def oauth_callback(code: str, state: str):
    """
    Handle OAuth2 callback from Google.
    @param code - Authorization code
    @param state - State parameter (contains customer_id)
    @returns Redirect or success message
    """
    global oauth2_handler
    if oauth2_handler is None:
        raise HTTPException(status_code=400, detail="OAuth2 not configured")

    try:
        print(f"[OAUTH CALLBACK] Received code and state: {state[:20]}...")
        result = oauth2_handler.handle_callback(code, state)
        customer_id = result.get('customer_id')
        calendar_email = result.get('calendar_email')
        print(f"[OAUTH CALLBACK] Success! customer_id={customer_id}, calendar_email={calendar_email}")
        
        # Redirigir a una página del frontend que notifique al padre
        frontend_url = os.getenv("OAUTH_SUCCESS_REDIRECT_URL", "http://localhost:5173/oauth-success")
        redirect_url = f"{frontend_url}?customer_id={customer_id}&status=success&calendar_email={calendar_email or ''}"
        return RedirectResponse(url=redirect_url)
    except Exception as e:
        print(f"[OAUTH CALLBACK] ERROR: {str(e)}")
        frontend_url = os.getenv("OAUTH_ERROR_REDIRECT_URL", "http://localhost:5173/oauth-error")
        error_url = f"{frontend_url}?error={str(e)}"
        return RedirectResponse(url=error_url)


@app.get("/oauth/status/{customer_id}")
async def oauth_status(customer_id: str):
    """
    Get OAuth2 connection status for a customer.
    @param customer_id - Customer identifier
    @returns Connection status
    """
    global oauth2_handler
    if oauth2_handler is None:
        return {"connected": False, "customer_id": customer_id, "error": "OAuth2 not configured"}

    try:
        return oauth2_handler.get_connection_status(customer_id)
    except Exception as e:
        return {"connected": False, "customer_id": customer_id, "error": str(e)}


@app.post("/oauth/disconnect")
async def oauth_disconnect(request: OAuthDisconnectRequest):
    """
    Disconnect Google Calendar for a customer.
    @param request - Request with customer_id
    @returns Success status
    """
    global oauth2_handler
    if oauth2_handler is None:
        raise HTTPException(status_code=400, detail="OAuth2 not configured")

    try:
        return oauth2_handler.disconnect(request.customer_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp")
async def mcp_endpoint(request: MCPRequest, x_customer_id: str | None = Header(None, alias="X-Customer-Id")):
    """Handle MCP JSON-RPC requests."""
    global backend, oauth2_handler
    if backend is None:
        backend = get_backend()
    # Asegurar que oauth2_handler esté disponible si el backend lo necesita
    if hasattr(backend, '_oauth2_handler') and backend._oauth2_handler and not oauth2_handler:
        oauth2_handler = backend._oauth2_handler

    method = request.method
    params = request.params or {}

    try:
        if method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            # customer_id puede venir del header X-Customer-Id o de los arguments
            customer_id = x_customer_id or arguments.get("customer_id")
            
            # Debug: imprimir customer_id recibido
            print(f"[MCP] Tool: {tool_name}, customer_id: {customer_id}, x_customer_id: {x_customer_id}")

            if tool_name == "check_availability":
                result = backend.check_availability(
                    date_iso=arguments["date_iso"],
                    start_time_iso=arguments["start_time_iso"],
                    end_time_iso=arguments["end_time_iso"],
                    customer_id=customer_id if hasattr(backend, "_get_service") else None,
                )
                result = {"available": result}
            elif tool_name == "get_available_slots":
                slots = backend.get_available_slots(
                    date_iso=arguments["date_iso"],
                    customer_id=customer_id if hasattr(backend, "_get_service") else None,
                )
                result = {"slots": slots}
            elif tool_name == "create_booking":
                booking_result = backend.create_booking(
                    customer_id=arguments["customer_id"],
                    customer_name=arguments["customer_name"],
                    date_iso=arguments["date_iso"],
                    start_time_iso=arguments["start_time_iso"],
                    end_time_iso=arguments["end_time_iso"],
                )
                result = booking_result
            elif tool_name == "get_booking":
                result = backend.get_booking(
                    booking_id=arguments["booking_id"],
                    customer_id=customer_id if hasattr(backend, "_get_service") else None,
                )
                if result is None:
                    result = {"booking": None}
            elif tool_name == "list_bookings":
                bookings_result = backend.list_bookings(customer_id=arguments["customer_id"])
                result = bookings_result
            elif tool_name == "update_booking":
                booking_result = backend.update_booking(
                    booking_id=arguments["booking_id"],
                    date_iso=arguments.get("date_iso"),
                    start_time_iso=arguments.get("start_time_iso"),
                    end_time_iso=arguments.get("end_time_iso"),
                    status=arguments.get("status"),
                    customer_id=customer_id if hasattr(backend, "_get_service") else None,
                )
                result = booking_result if booking_result is not None else {"booking": None}
            elif tool_name == "delete_booking":
                success = backend.delete_booking(
                    booking_id=arguments["booking_id"],
                    customer_id=customer_id if hasattr(backend, "_get_service") else None,
                )
                result = {"success": success}
            else:
                return MCPResponse(
                    id=request.id,
                    error={"code": -32601, "message": f"Unknown tool: {tool_name}"},
                )

            return MCPResponse(id=request.id, result=result)
        else:
            return MCPResponse(
                id=request.id,
                error={"code": -32601, "message": f"Unknown method: {method}"},
            )
    except KeyError as e:
        return MCPResponse(
            id=request.id,
            error={"code": -32602, "message": f"Missing parameter: {e}"},
        )
    except Exception as e:
        return MCPResponse(
            id=request.id,
            error={"code": -32603, "message": f"Internal error: {str(e)}"},
        )


@app.get("/health")
async def health():
    """Health check endpoint."""
    backend_type = os.getenv("CALENDAR_BACKEND", "sqlite")
    oauth_configured = os.getenv("GOOGLE_OAUTH_CLIENT_ID") is not None
    return {
        "status": "ok",
        "service": "mcp-calendar-server",
        "backend": backend_type,
        "oauth_configured": oauth_configured,
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("CALENDAR_SERVER_PORT", "60000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
