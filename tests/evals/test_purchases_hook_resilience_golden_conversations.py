from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from ai_assistants.adapters.external_hook import ExternalHookConfig, ExternalHookPurchasesAdapter
from ai_assistants.adapters.registry import set_purchases_adapter
from ai_assistants.orchestrator.runtime import Orchestrator
from ai_assistants.persistence.conversation_store import InMemoryConversationStore
from tests.evals.golden import assert_golden


@pytest.fixture(autouse=True)
def _eval_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_ASSISTANTS_LLM_ROUTER_ENABLED", "0")
    monkeypatch.setenv("AI_ASSISTANTS_LLM_NLG_ENABLED", "0")


@pytest.fixture()
def _reset_adapter() -> None:
    set_purchases_adapter(None)
    yield
    set_purchases_adapter(None)


def _make_orchestrator() -> Orchestrator:
    return Orchestrator(store=InMemoryConversationStore())


def test_golden_hook_unavailable_on_get_order(_reset_adapter: None) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=500, json={"ok": False})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    adapter = ExternalHookPurchasesAdapter(
        ExternalHookConfig(
            url="https://hook.example.test",
            timeout_seconds=1.0,
            api_key=None,
            signature_secret=None,
            max_retries=0,
        ),
        client=client,
    )
    set_purchases_adapter(adapter)

    orch = _make_orchestrator()
    result = orch.run_turn(
        conversation_id="whatsapp:+5491112345678",
        user_text="Revisar compra ORDER-200",
        event_id="eh1",
    )
    assert_golden(name="purchases_hook_unavailable_get_order", actual=result.response_text)


def test_golden_hook_unavailable_on_tracking_lookup(_reset_adapter: None) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timeout")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    adapter = ExternalHookPurchasesAdapter(
        ExternalHookConfig(
            url="https://hook.example.test",
            timeout_seconds=0.1,
            api_key=None,
            signature_secret=None,
            max_retries=0,
        ),
        client=client,
    )
    set_purchases_adapter(adapter)

    orch = _make_orchestrator()
    result = orch.run_turn(
        conversation_id="whatsapp:+5491112345678",
        user_text="TRACK-9001",
        event_id="eh2",
    )
    assert_golden(name="purchases_hook_unavailable_tracking", actual=result.response_text)


def test_golden_hook_unavailable_on_list_orders(_reset_adapter: None) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=503, json={"ok": False})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    adapter = ExternalHookPurchasesAdapter(
        ExternalHookConfig(
            url="https://hook.example.test",
            timeout_seconds=1.0,
            api_key=None,
            signature_secret=None,
            max_retries=0,
        ),
        client=client,
    )
    set_purchases_adapter(adapter)

    orch = _make_orchestrator()
    result = orch.run_turn(
        conversation_id="whatsapp:+5491112345678",
        user_text="mis compras",
        event_id="eh3",
    )
    assert_golden(name="purchases_hook_unavailable_list_orders", actual=result.response_text)


