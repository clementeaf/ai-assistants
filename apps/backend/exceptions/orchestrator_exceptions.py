from __future__ import annotations


class OrchestratorError(Exception):
    """Base exception for orchestrator-related errors."""

    pass


class ConversationNotFoundError(OrchestratorError):
    """Raised when a conversation is not found."""

    def __init__(self, conversation_id: str) -> None:
        super().__init__(f"Conversation not found: {conversation_id}")
        self.conversation_id = conversation_id


class EventAlreadyProcessedError(OrchestratorError):
    """Raised when an event has already been processed (idempotency)."""

    def __init__(self, event_id: str, conversation_id: str) -> None:
        super().__init__(f"Event already processed: {event_id} in conversation {conversation_id}")
        self.event_id = event_id
        self.conversation_id = conversation_id
