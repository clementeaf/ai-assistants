from __future__ import annotations

from dataclasses import dataclass

from langgraph.graph import StateGraph
from structlog.contextvars import get_contextvars

from ai_assistants.graphs.router_graph import GraphState, build_router_graph
from ai_assistants.nlg.rewriter import TextRewriter, build_rewriter_from_env, maybe_rewrite
from ai_assistants.observability.logging import get_logger
from ai_assistants.orchestrator.state import (
    ConversationState,
    MessageRole,
    append_message,
    get_last_assistant_text,
    is_event_processed,
    mark_event_processed,
)
from ai_assistants.persistence.conversation_store import ConversationStore
from ai_assistants.persistence.memory_store import CustomerMemoryStore


@dataclass(frozen=True, slots=True)
class TurnResult:
    """Result of a single conversation turn."""

    conversation_id: str
    response_text: str
    state: ConversationState


class Orchestrator:
    """Runs LangGraph graphs for conversation turns and persists state."""

    def __init__(
        self,
        store: ConversationStore,
        rewriter: TextRewriter | None = None,
        memory_store: CustomerMemoryStore | None = None,
    ) -> None:
        self._store = store
        self._logger = get_logger()
        self._graph: StateGraph[GraphState] = build_router_graph()
        self._compiled = self._graph.compile()
        self._rewriter = rewriter if rewriter is not None else build_rewriter_from_env()
        self._memory_store = memory_store

    def run_turn(
        self,
        conversation_id: str,
        user_text: str,
        event_id: str | None = None,
        customer_id: str | None = None,
    ) -> TurnResult:
        """Run a full user->assistant turn and persist the resulting state.

        If event_id is provided, the orchestrator ensures idempotency for retries.
        """
        state = self._store.get(conversation_id)
        if state is None:
            state = ConversationState(conversation_id=conversation_id)
        if customer_id is not None:
            state = state.model_copy(update={"customer_id": customer_id})

        # Load long-term memory (per project + customer) into state.
        if self._memory_store is not None and state.customer_id is not None:
            ctx = get_contextvars()
            project_id = ctx.get("project_id")
            resolved_project_id = project_id if isinstance(project_id, str) and project_id.strip() != "" else "dev"
            memory = self._memory_store.get(project_id=resolved_project_id, customer_id=state.customer_id)
            if memory is not None:
                state = state.model_copy(update={"customer_memory": memory.data})

        if event_id is not None and is_event_processed(state, event_id):
            cached = get_last_assistant_text(state) or "Evento duplicado; no generé una respuesta nueva."
            self._logger.info("turn.duplicate", conversation_id=conversation_id, event_id=event_id)
            return TurnResult(conversation_id=conversation_id, response_text=cached, state=state)

        state = append_message(state, role=MessageRole.user, text=user_text)

        graph_state: GraphState = {
            "conversation": state,
            "user_text": user_text,
            "domain": "unknown",
            "response_text": "",
        }
        self._logger.info("turn.start", conversation_id=conversation_id)
        final_state: GraphState = self._compiled.invoke(graph_state)
        draft_text = final_state["response_text"] or "No pude generar una respuesta."
        response_text = maybe_rewrite(
            rewriter=self._rewriter,
            user_text=user_text,
            draft_text=draft_text,
            domain=final_state["domain"],
        )

        updated_state = append_message(final_state["conversation"], role=MessageRole.assistant, text=response_text)
        if event_id is not None:
            updated_state = mark_event_processed(updated_state, event_id)
        self._store.put(updated_state)

        # Persist long-term memory after the turn.
        if self._memory_store is not None and updated_state.customer_id is not None:
            ctx = get_contextvars()
            project_id = ctx.get("project_id")
            resolved_project_id = project_id if isinstance(project_id, str) and project_id.strip() != "" else "dev"
            to_save: dict[str, str] = dict(updated_state.customer_memory)
            if updated_state.last_order_id is not None:
                to_save["last_order_id"] = updated_state.last_order_id
            if updated_state.last_tracking_id is not None:
                to_save["last_tracking_id"] = updated_state.last_tracking_id
            self._memory_store.upsert(
                project_id=resolved_project_id,
                customer_id=updated_state.customer_id,
                data=to_save,
            )
        self._logger.info(
            "turn.end",
            conversation_id=conversation_id,
            domain=final_state["domain"],
        )
        return TurnResult(conversation_id=conversation_id, response_text=response_text, state=updated_state)


