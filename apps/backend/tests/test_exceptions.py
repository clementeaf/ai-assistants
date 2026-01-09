"""Tests for custom exceptions."""

from __future__ import annotations

import pytest

from ai_assistants.exceptions.adapter_exceptions import (
    AdapterError,
    AdapterTimeoutError,
    AdapterUnavailableError,
)
from ai_assistants.exceptions.api_exceptions import (
    APIError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
)
from ai_assistants.exceptions.orchestrator_exceptions import (
    ConversationNotFoundError,
    EventAlreadyProcessedError,
    OrchestratorError,
)


def test_adapter_exceptions() -> None:
    """Test adapter exception hierarchy."""
    assert issubclass(AdapterUnavailableError, AdapterError)
    assert issubclass(AdapterTimeoutError, AdapterError)
    
    error = AdapterUnavailableError("Service unavailable", adapter_name="test")
    assert error.adapter_name == "test"
    
    timeout_error = AdapterTimeoutError("Timeout", timeout_seconds=30.0)
    assert timeout_error.timeout_seconds == 30.0


def test_api_exceptions() -> None:
    """Test API exception hierarchy."""
    assert issubclass(AuthenticationError, APIError)
    assert issubclass(RateLimitError, APIError)
    assert issubclass(ValidationError, APIError)
    
    validation_error = ValidationError("Invalid input", field="email")
    assert validation_error.field == "email"


def test_orchestrator_exceptions() -> None:
    """Test orchestrator exception hierarchy."""
    assert issubclass(ConversationNotFoundError, OrchestratorError)
    assert issubclass(EventAlreadyProcessedError, OrchestratorError)
    
    conv_error = ConversationNotFoundError("conv-123")
    assert conv_error.conversation_id == "conv-123"
    
    event_error = EventAlreadyProcessedError("event-456", "conv-123")
    assert event_error.event_id == "event-456"
    assert event_error.conversation_id == "conv-123"
