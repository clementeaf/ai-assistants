"""Tests for the orchestrator component."""

from __future__ import annotations

from ai_assistants.orchestrator.runtime import Orchestrator
from ai_assistants.orchestrator.state import ConversationState, MessageRole


def test_orchestrator_run_turn_basic(conversation_store, memory_store) -> None:
    """Test basic orchestrator turn execution."""
    orchestrator = Orchestrator(store=conversation_store, memory_store=memory_store)
    
    conversation_id = "test:conversation"
    user_text = "Hola"
    
    result = orchestrator.run_turn(
        conversation_id=conversation_id,
        user_text=user_text,
    )
    
    assert result.conversation_id == conversation_id
    assert result.response_text is not None
    assert len(result.response_text) > 0
    
    stored_state = conversation_store.get(conversation_id)
    assert stored_state is not None
    assert len(stored_state.messages) == 2
    assert stored_state.messages[0].role == MessageRole.user
    assert stored_state.messages[0].text == user_text
    assert stored_state.messages[1].role == MessageRole.assistant


def test_orchestrator_idempotency(conversation_store, memory_store) -> None:
    """Test that orchestrator handles duplicate events correctly."""
    orchestrator = Orchestrator(store=conversation_store, memory_store=memory_store)
    
    conversation_id = "test:idempotency"
    user_text = "Test message"
    event_id = "event-123"
    
    result1 = orchestrator.run_turn(
        conversation_id=conversation_id,
        user_text=user_text,
        event_id=event_id,
    )
    
    result2 = orchestrator.run_turn(
        conversation_id=conversation_id,
        user_text=user_text,
        event_id=event_id,
    )
    
    assert result1.response_text == result2.response_text
    assert result2.response_text == "Evento duplicado; no generé una respuesta nueva."
    
    stored_state = conversation_store.get(conversation_id)
    assert stored_state is not None
    assert event_id in stored_state.processed_event_ids


def test_orchestrator_customer_memory(conversation_store, memory_store) -> None:
    """Test that orchestrator persists customer memory."""
    orchestrator = Orchestrator(store=conversation_store, memory_store=memory_store)
    
    conversation_id = "test:memory"
    customer_id = "customer-123"
    
    result = orchestrator.run_turn(
        conversation_id=conversation_id,
        user_text="Hola",
        customer_id=customer_id,
    )
    
    stored_state = conversation_store.get(conversation_id)
    assert stored_state is not None
    assert stored_state.customer_id == customer_id
    
    memory = memory_store.get(project_id="dev", customer_id=customer_id)
    assert memory is not None
