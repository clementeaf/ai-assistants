from __future__ import annotations

import json
from datetime import datetime, timezone

import httpx
from structlog.contextvars import bind_contextvars, clear_contextvars

from ai_assistants.adapters.external_hook import ExternalHookConfig, ExternalHookPurchasesAdapter
from ai_assistants.channels.webhook_security import compute_signature


def test_external_hook_adapter_get_order() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8"))
        assert body["action"] == "get_order"
        assert body["payload"]["order_id"] == "ORDER-200"
        return httpx.Response(
            status_code=200,
            json={
                "ok": True,
                "order": {
                    "order_id": "ORDER-200",
                    "customer_id": "+5491112345678",
                    "status": "shipped",
                    "total_amount": 120.0,
                    "currency": "USD",
                    "created_at_iso": datetime(2025, 2, 10, 16, 30, tzinfo=timezone.utc).isoformat(),
                },
            },
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    adapter = ExternalHookPurchasesAdapter(
        ExternalHookConfig(
            url="https://hook.example.test",
            timeout_seconds=2.0,
            api_key=None,
            signature_secret=None,
            max_retries=0,
        ),
        client=client,
    )

    order = adapter.get_order("ORDER-200")
    assert order is not None
    assert order.order_id == "ORDER-200"
    assert order.status.value == "shipped"


def test_external_hook_adapter_sends_signature_headers_when_configured() -> None:
    fixed_ts = 1700000000

    def handler(request: httpx.Request) -> httpx.Response:
        body_bytes = request.content
        assert request.headers.get("X-Hook-Timestamp") == str(fixed_ts)
        assert request.headers.get("X-Hook-Signature") == compute_signature("secret", str(fixed_ts), body_bytes)
        return httpx.Response(status_code=200, json={"ok": False})

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    adapter = ExternalHookPurchasesAdapter(
        ExternalHookConfig(
            url="https://hook.example.test",
            timeout_seconds=2.0,
            api_key=None,
            signature_secret="secret",
            max_retries=0,
        ),
        client=client,
        now_fn=lambda: float(fixed_ts),
    )

    assert adapter.get_order("ORDER-404") is None


def test_external_hook_adapter_propagates_request_id() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("X-Request-Id") == "rid-123"
        assert request.headers.get("X-Project-Id") == "proj-1"
        return httpx.Response(status_code=200, json={"ok": False})

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    adapter = ExternalHookPurchasesAdapter(
        ExternalHookConfig(
            url="https://hook.example.test",
            timeout_seconds=2.0,
            api_key=None,
            signature_secret=None,
            max_retries=0,
        ),
        client=client,
    )

    bind_contextvars(request_id="rid-123", project_id="proj-1")
    try:
        assert adapter.get_order("ORDER-404") is None
    finally:
        clear_contextvars()

