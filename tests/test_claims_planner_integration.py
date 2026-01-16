from __future__ import annotations

import pytest
from ai_assistants.automata.claims.planner import AskUserAction, ClaimsPlanner, PlannerOutput, ToolCallAction
from ai_assistants.automata.claims.runtime import set_claims_planner
from ai_assistants.orchestrator.runtime import Orchestrator
from ai_assistants.persistence.sqlite_memory_store import SqliteCustomerMemoryStore, load_sqlite_memory_store_config
from ai_assistants.persistence.sqlite_store import SqliteConversationStore, load_sqlite_store_config


class _StubPlanner(ClaimsPlanner):
    def __init__(self, plan: PlannerOutput) -> None:
        from ai_assistants.llm.openai_compatible import OpenAICompatibleClient, OpenAICompatibleConfig

        super().__init__(OpenAICompatibleClient(OpenAICompatibleConfig("", "", "", 10.0)))
        self._plan = plan

    def plan(self, *, user_text: str, customer_id: str | None) -> PlannerOutput | None:
        return self._plan


@pytest.fixture()
def orch() -> Orchestrator:
    store = SqliteConversationStore(load_sqlite_store_config())
    memory_store = SqliteCustomerMemoryStore(load_sqlite_memory_store_config())
    return Orchestrator(store=store, memory_store=memory_store)


def test_planner_ask_user_short_circuits(orch: Orchestrator) -> None:
    plan = PlannerOutput.model_validate(
        {
            "kind": "plan",
            "actions": [{"type": "ask_user", "text": "Contame el problema y el ID de orden si aplica."}],
        }
    )
    set_claims_planner(_StubPlanner(plan))
    try:
        out = orch.run_turn(
            conversation_id="web:claims_test1", user_text="quiero hacer un reclamo", event_id="c1", customer_id="+5491112345678"
        )
        assert "problema" in out.response_text.lower() or "orden" in out.response_text.lower()
    finally:
        set_claims_planner(None)


def test_planner_get_order(orch: Orchestrator) -> None:
    plan = PlannerOutput.model_validate(
        {
            "kind": "plan",
            "actions": [{"type": "tool_call", "tool": "get_order", "args": {"order_id": "ORDER-100"}}],
        }
    )
    set_claims_planner(_StubPlanner(plan))
    try:
        out = orch.run_turn(
            conversation_id="web:claims_test2",
            user_text="quiero hacer un reclamo sobre ORDER-100",
            event_id="c2",
            customer_id="+5491112345678",
        )
        assert "ORDER-100" in out.response_text
        assert "reclamo" in out.response_text.lower() or "problema" in out.response_text.lower()
    finally:
        set_claims_planner(None)


def test_planner_explicit_order_id_deterministic(orch: Orchestrator) -> None:
    set_claims_planner(None)
    out = orch.run_turn(
        conversation_id="web:claims_test3",
        user_text="quiero hacer un reclamo sobre ORDER-100",
        event_id="c3",
        customer_id="+5491112345678",
    )
    assert "ORDER-100" in out.response_text
    assert "reclamo" in out.response_text.lower() or "problema" in out.response_text.lower()


def test_planner_disabled_fallback(orch: Orchestrator) -> None:
    set_claims_planner(None)
    out = orch.run_turn(
        conversation_id="web:claims_test4", user_text="quiero hacer un reclamo", event_id="c4", customer_id="+5491112345678"
    )
    assert "reclamo" in out.response_text.lower() or "problema" in out.response_text.lower() or "orden" in out.response_text.lower()

