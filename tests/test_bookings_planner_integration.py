from __future__ import annotations

import pytest
from ai_assistants.automata.bookings.planner import AskUserAction, BookingsPlanner, PlannerOutput, ToolCallAction
from ai_assistants.automata.bookings.runtime import set_bookings_planner
from ai_assistants.orchestrator.runtime import Orchestrator
from ai_assistants.persistence.sqlite_memory_store import SqliteCustomerMemoryStore, load_sqlite_memory_store_config
from ai_assistants.persistence.sqlite_store import SqliteConversationStore, load_sqlite_store_config


class _StubPlanner(BookingsPlanner):
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
            "actions": [{"type": "ask_user", "text": "¿Qué fecha y horario necesitás para la reserva?"}],
        }
    )
    set_bookings_planner(_StubPlanner(plan))
    try:
        out = orch.run_turn(
            conversation_id="web:bookings_test1", user_text="quiero hacer una reserva", event_id="b1", customer_id="+5491112345678"
        )
        assert "fecha" in out.response_text.lower() or "horario" in out.response_text.lower()
    finally:
        set_bookings_planner(None)


def test_planner_vector_recall(orch: Orchestrator) -> None:
    plan = PlannerOutput.model_validate(
        {
            "kind": "plan",
            "actions": [{"type": "tool_call", "tool": "vector_recall", "args": {"query": "reserva", "k": 3}}],
        }
    )
    set_bookings_planner(_StubPlanner(plan))
    try:
        out = orch.run_turn(
            conversation_id="web:bookings_test2",
            user_text="quiero ver mis reservas",
            event_id="b2",
            customer_id="+5491112345678",
        )
        # Should fallback to simple response if vector memory is not enabled
        assert len(out.response_text) > 0
    finally:
        set_bookings_planner(None)


def test_planner_disabled_fallback(orch: Orchestrator) -> None:
    set_bookings_planner(None)
    out = orch.run_turn(
        conversation_id="web:bookings_test3", user_text="quiero hacer una reserva", event_id="b3", customer_id="+5491112345678"
    )
    assert "reserva" in out.response_text.lower() or "fecha" in out.response_text.lower()

