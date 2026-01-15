"""Tests for autonomous LLM node functionality."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch

from ai_assistants.graphs.router_graph import GraphState, autonomous_node
from ai_assistants.orchestrator.state import ConversationState, ConversationMessage, MessageRole
from ai_assistants.routing.autonomous_config import AutonomousConfig


@pytest.fixture()
def base_state() -> GraphState:
    """Create a base graph state for testing."""
    conversation = ConversationState(conversation_id="test:conversation")
    return {
        "conversation": conversation,
        "user_text": "Hola, ¿cómo estás?",
        "domain": "autonomous",
        "response_text": "",
    }


def test_autonomous_node_disabled_fallback(base_state: GraphState, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that autonomous node falls back to unknown when disabled."""
    monkeypatch.setenv("AI_ASSISTANTS_AUTONOMOUS_ENABLED", "0")
    
    result = autonomous_node(base_state)
    
    assert "reserva" in result["response_text"].lower() or "menu" in result["response_text"].lower()


def test_autonomous_node_missing_llm_config_fallback(base_state: GraphState, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that autonomous node falls back when LLM config is missing."""
    monkeypatch.setenv("AI_ASSISTANTS_AUTONOMOUS_ENABLED", "1")
    monkeypatch.delenv("AI_ASSISTANTS_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("AI_ASSISTANTS_LLM_API_KEY", raising=False)
    monkeypatch.delenv("AI_ASSISTANTS_LLM_MODEL", raising=False)
    
    result = autonomous_node(base_state)
    
    assert "reserva" in result["response_text"].lower() or "menu" in result["response_text"].lower()


@patch("ai_assistants.graphs.router_graph.OpenAICompatibleClient")
def test_autonomous_node_success(mock_client_class: Mock, base_state: GraphState, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test successful autonomous node execution."""
    monkeypatch.setenv("AI_ASSISTANTS_AUTONOMOUS_ENABLED", "1")
    monkeypatch.setenv("AI_ASSISTANTS_LLM_BASE_URL", "https://api.openai.com")
    monkeypatch.setenv("AI_ASSISTANTS_LLM_API_KEY", "test-key")
    monkeypatch.setenv("AI_ASSISTANTS_LLM_MODEL", "gpt-4o-mini")
    
    mock_client = Mock()
    mock_client.chat_completion.return_value = "¡Hola! Estoy bien, gracias por preguntar. ¿En qué puedo ayudarte?"
    mock_client_class.return_value = mock_client
    
    result = autonomous_node(base_state)
    
    assert result["response_text"] == "¡Hola! Estoy bien, gracias por preguntar. ¿En qué puedo ayudarte?"
    assert mock_client.chat_completion.called
    call_args = mock_client.chat_completion.call_args
    assert call_args is not None
    assert "system" in call_args.kwargs
    assert "user" in call_args.kwargs
    assert "User: Hola, ¿cómo estás?" in call_args.kwargs["user"]


@patch("ai_assistants.graphs.router_graph.OpenAICompatibleClient")
def test_autonomous_node_uses_conversation_history(mock_client_class: Mock, base_state: GraphState, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that autonomous node includes conversation history."""
    monkeypatch.setenv("AI_ASSISTANTS_AUTONOMOUS_ENABLED", "1")
    monkeypatch.setenv("AI_ASSISTANTS_LLM_BASE_URL", "https://api.openai.com")
    monkeypatch.setenv("AI_ASSISTANTS_LLM_API_KEY", "test-key")
    monkeypatch.setenv("AI_ASSISTANTS_LLM_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("AI_ASSISTANTS_AUTONOMOUS_MAX_HISTORY", "5")
    
    conversation = base_state["conversation"]
    conversation.messages = [
        ConversationMessage(role=MessageRole.user, text="Primer mensaje", created_at_iso="2025-01-01T00:00:00Z"),
        ConversationMessage(role=MessageRole.assistant, text="Primera respuesta", created_at_iso="2025-01-01T00:01:00Z"),
        ConversationMessage(role=MessageRole.user, text="Segundo mensaje", created_at_iso="2025-01-01T00:02:00Z"),
    ]
    base_state["conversation"] = conversation
    
    mock_client = Mock()
    mock_client.chat_completion.return_value = "Respuesta final"
    mock_client_class.return_value = mock_client
    
    result = autonomous_node(base_state)
    
    assert result["response_text"] == "Respuesta final"
    call_args = mock_client.chat_completion.call_args
    assert call_args is not None
    user_prompt = call_args.kwargs["user"]
    assert "User: Primer mensaje" in user_prompt
    assert "Assistant: Primera respuesta" in user_prompt
    assert "User: Segundo mensaje" in user_prompt
    assert "User: Hola, ¿cómo estás?" in user_prompt


@patch("ai_assistants.graphs.router_graph.OpenAICompatibleClient")
def test_autonomous_node_empty_response_fallback(mock_client_class: Mock, base_state: GraphState, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that autonomous node falls back when LLM returns empty response."""
    monkeypatch.setenv("AI_ASSISTANTS_AUTONOMOUS_ENABLED", "1")
    monkeypatch.setenv("AI_ASSISTANTS_LLM_BASE_URL", "https://api.openai.com")
    monkeypatch.setenv("AI_ASSISTANTS_LLM_API_KEY", "test-key")
    monkeypatch.setenv("AI_ASSISTANTS_LLM_MODEL", "gpt-4o-mini")
    
    mock_client = Mock()
    mock_client.chat_completion.return_value = ""
    mock_client_class.return_value = mock_client
    
    result = autonomous_node(base_state)
    
    assert "reserva" in result["response_text"].lower() or "menu" in result["response_text"].lower()


@patch("ai_assistants.graphs.router_graph.OpenAICompatibleClient")
def test_autonomous_node_error_fallback(mock_client_class: Mock, base_state: GraphState, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that autonomous node falls back on LLM errors."""
    monkeypatch.setenv("AI_ASSISTANTS_AUTONOMOUS_ENABLED", "1")
    monkeypatch.setenv("AI_ASSISTANTS_LLM_BASE_URL", "https://api.openai.com")
    monkeypatch.setenv("AI_ASSISTANTS_LLM_API_KEY", "test-key")
    monkeypatch.setenv("AI_ASSISTANTS_LLM_MODEL", "gpt-4o-mini")
    
    mock_client = Mock()
    mock_client.chat_completion.side_effect = Exception("LLM error")
    mock_client_class.return_value = mock_client
    
    result = autonomous_node(base_state)
    
    assert "reserva" in result["response_text"].lower() or "menu" in result["response_text"].lower()
