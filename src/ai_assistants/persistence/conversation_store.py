from __future__ import annotations

from collections.abc import MutableMapping

from ai_assistants.orchestrator.state import ConversationState


class ConversationStore:
    """Conversation state storage abstraction."""

    def get(self, conversation_id: str) -> ConversationState | None:
        """Return state for the given conversation id if present."""
        raise NotImplementedError

    def put(self, state: ConversationState) -> None:
        """Persist the provided state."""
        raise NotImplementedError


class InMemoryConversationStore(ConversationStore):
    """In-memory conversation store for local development and testing."""

    def __init__(self) -> None:
        self._by_id: MutableMapping[str, ConversationState] = {}

    def get(self, conversation_id: str) -> ConversationState | None:
        """Return state for the given conversation id if present."""
        return self._by_id.get(conversation_id)

    def put(self, state: ConversationState) -> None:
        """Persist the provided state in memory."""
        self._by_id[state.conversation_id] = state


