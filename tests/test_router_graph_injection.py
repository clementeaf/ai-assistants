from __future__ import annotations

import pytest

from ai_assistants.graphs.router_graph import GraphState, build_router_graph
from ai_assistants.orchestrator.state import ConversationState


def test_router_graph_injection_routes_track_to_purchases() -> None:
    graph = build_router_graph(router_fn=lambda _text: "purchases").compile()
    state: GraphState = {
        "conversation": ConversationState(conversation_id="whatsapp:+5491112345678"),
        "user_text": "TRACK-9001",
        "domain": "unknown",
        "response_text": "",
    }
    out = graph.invoke(state)
    assert out["domain"] == "purchases"
    assert "Tracking TRACK-9001" in out["response_text"]


def test_router_graph_injection_routes_to_unknown() -> None:
    graph = build_router_graph(router_fn=lambda _text: "unknown").compile()
    state: GraphState = {
        "conversation": ConversationState(conversation_id="whatsapp:+5491112345678"),
        "user_text": "TRACK-9001",
        "domain": "unknown",
        "response_text": "",
    }
    out = graph.invoke(state)
    assert out["domain"] == "unknown"
    assert "¿Querés hacer una reserva" in out["response_text"]


