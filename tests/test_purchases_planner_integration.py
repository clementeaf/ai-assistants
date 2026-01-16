from __future__ import annotations

import pytest

from ai_assistants.automata.purchases.planner import PlannerOutput
from ai_assistants.automata.purchases.runtime import set_purchases_planner
from ai_assistants.orchestrator.runtime import Orchestrator
from ai_assistants.persistence.sqlite_store import SqliteConversationStore, load_sqlite_store_config
from ai_assistants.persistence.sqlite_memory_store import SqliteCustomerMemoryStore, load_sqlite_memory_store_config


class _StubPlanner:
    def __init__(self, plan: PlannerOutput) -> None:
        self._plan = plan

    def plan(self, *, user_text: str, customer_id: str | None, last_order_id: str | None, last_tracking_id: str | None) -> PlannerOutput:
        return self._plan


@pytest.fixture()
def orch(tmp_path, monkeypatch: pytest.MonkeyPatch) -> Orchestrator:
    db_path = tmp_path / "test.sqlite3"
    monkeypatch.setenv("AI_ASSISTANTS_SQLITE_PATH", str(db_path))
    store = SqliteConversationStore(load_sqlite_store_config())
    mem = SqliteCustomerMemoryStore(load_sqlite_memory_store_config())
    return Orchestrator(store=store, memory_store=mem)


def test_planner_tool_call_get_order_executes(orch: Orchestrator) -> None:
    plan = PlannerOutput.model_validate(
        {
            "kind": "plan",
            "actions": [{"type": "tool_call", "tool": "get_order", "args": {"order_id": "ORDER-100"}}],
        }
    )
    set_purchases_planner(_StubPlanner(plan))
    try:
        out = orch.run_turn(conversation_id="web:demo", user_text="donde esta mi compra", event_id="e1", customer_id="+5491112345678")
        assert "Orden ORDER-100" in out.response_text
    finally:
        set_purchases_planner(None)


def test_planner_ask_user_short_circuits(orch: Orchestrator) -> None:
    plan = PlannerOutput.model_validate(
        {
            "kind": "plan",
            "actions": [{"type": "ask_user", "text": "¿Tenés el ORDER-XXX o TRACK-XXX?"}],
        }
    )
    set_purchases_planner(_StubPlanner(plan))
    try:
        out = orch.run_turn(
            conversation_id="web:demo",
            user_text="necesito ayuda con una compra",
            event_id="e2",
            customer_id="+5491112345678",
        )
        assert out.response_text == "¿Tenés el ORDER-XXX o TRACK-XXX?"
    finally:
        set_purchases_planner(None)


