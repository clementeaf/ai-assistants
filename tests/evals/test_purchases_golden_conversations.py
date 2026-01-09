from __future__ import annotations

from pathlib import Path

import pytest

from ai_assistants.orchestrator.runtime import Orchestrator
from ai_assistants.persistence.conversation_store import InMemoryConversationStore
from tests.evals.golden import assert_golden


@pytest.fixture(autouse=True)
def _eval_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_ASSISTANTS_LLM_ROUTER_ENABLED", "0")
    monkeypatch.setenv("AI_ASSISTANTS_LLM_NLG_ENABLED", "0")
    monkeypatch.setenv("AI_ASSISTANTS_VECTOR_MEMORY_ENABLED", "0")
    monkeypatch.setenv("AI_ASSISTANTS_FIXED_NOW_ISO", "2025-03-15T00:00:00+00:00")
    monkeypatch.delenv("AI_ASSISTANTS_PURCHASES_HOOK_URL", raising=False)
    monkeypatch.delenv("AI_ASSISTANTS_PURCHASES_HOOK_API_KEY", raising=False)
    monkeypatch.delenv("AI_ASSISTANTS_PURCHASES_HOOK_SIGNATURE_SECRET", raising=False)
    monkeypatch.delenv("AI_ASSISTANTS_PURCHASES_HOOK_MAX_RETRIES", raising=False)


def _make_orchestrator() -> Orchestrator:
    from ai_assistants.persistence.sqlite_memory_store import SqliteCustomerMemoryStore, SqliteMemoryStoreConfig
    from ai_assistants.adapters.registry import set_purchases_adapter
    from ai_assistants.adapters.demo_purchases import DemoPurchasesAdapter

    # keep evals deterministic
    set_purchases_adapter(DemoPurchasesAdapter())
    memory_store = SqliteCustomerMemoryStore(SqliteMemoryStoreConfig(path=Path(":memory:")))
    return Orchestrator(store=InMemoryConversationStore(), memory_store=memory_store)


def test_golden_tracking_by_order_id_whatsapp_inferred_customer() -> None:
    orch = _make_orchestrator()
    result = orch.run_turn(
        conversation_id="whatsapp:+5491112345678",
        user_text="Seguimiento de ORDER-200",
        event_id="m1",
    )
    assert_golden(name="purchases_tracking_by_order_id", actual=result.response_text)


def test_golden_tracking_by_tracking_id() -> None:
    orch = _make_orchestrator()
    result = orch.run_turn(
        conversation_id="whatsapp:+5491112345678",
        user_text="TRACK-9001",
        event_id="m2",
    )
    assert_golden(name="purchases_tracking_by_tracking_id", actual=result.response_text)


def test_golden_list_orders_whatsapp() -> None:
    orch = _make_orchestrator()
    result = orch.run_turn(
        conversation_id="whatsapp:+5491112345678",
        user_text="mis compras",
        event_id="m3",
    )
    assert_golden(name="purchases_list_orders", actual=result.response_text)


def test_golden_list_orders_web_requires_customer_id() -> None:
    orch = _make_orchestrator()
    result = orch.run_turn(conversation_id="web:demo", user_text="mis compras", event_id="m4")
    assert_golden(name="purchases_list_orders_missing_customer", actual=result.response_text)


def test_golden_list_orders_web_with_customer_id() -> None:
    orch = _make_orchestrator()
    result = orch.run_turn(
        conversation_id="web:demo",
        user_text="mis compras",
        event_id="m5",
        customer_id="+5491112345678",
    )
    assert_golden(name="purchases_list_orders_web_customer", actual=result.response_text)


def test_golden_order_not_found() -> None:
    orch = _make_orchestrator()
    result = orch.run_turn(
        conversation_id="whatsapp:+5491112345678",
        user_text="Revisar compra ORDER-999",
        event_id="m6",
    )
    assert_golden(name="purchases_order_not_found", actual=result.response_text)


def test_golden_missing_identifiers() -> None:
    orch = _make_orchestrator()
    result = orch.run_turn(
        conversation_id="whatsapp:+5491112345678",
        user_text="Quiero saber el estado de mi compra",
        event_id="m7",
    )
    assert_golden(name="purchases_missing_identifiers", actual=result.response_text)


def test_golden_idempotent_retry_returns_same_response() -> None:
    orch = _make_orchestrator()
    first = orch.run_turn(
        conversation_id="whatsapp:+5491112345678",
        user_text="TRACK-9002",
        event_id="m8",
    )
    second = orch.run_turn(
        conversation_id="whatsapp:+5491112345678",
        user_text="TRACK-9002",
        event_id="m8",
    )
    assert first.response_text == second.response_text


def test_golden_followup_tracking_uses_memory() -> None:
    orch = _make_orchestrator()
    first = orch.run_turn(
        conversation_id="whatsapp:+5491112345678",
        user_text="Seguimiento de ORDER-200",
        event_id="m9",
    )
    assert "ORDER-200" in first.response_text

    follow = orch.run_turn(
        conversation_id="whatsapp:+5491112345678",
        user_text="y el seguimiento?",
        event_id="m10",
    )
    assert_golden(name="purchases_followup_tracking_memory", actual=follow.response_text)


def test_golden_last_month_candidates() -> None:
    orch = _make_orchestrator()
    result = orch.run_turn(
        conversation_id="whatsapp:+5491112345678",
        user_text="Creo que pedí esto el mes pasado",
        event_id="m11",
    )
    assert_golden(name="purchases_last_month_candidates", actual=result.response_text)


def test_golden_last_month_disambiguated_by_amount() -> None:
    orch = _make_orchestrator()
    result = orch.run_turn(
        conversation_id="whatsapp:+5491112345678",
        user_text="Creo que pedí esto el mes pasado, fue 120",
        event_id="m12",
    )
    assert_golden(name="purchases_tracking_by_order_id", actual=result.response_text)


