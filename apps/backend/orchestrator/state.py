from __future__ import annotations

import os
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Role of a conversation message."""

    user = "user"
    assistant = "assistant"
    system = "system"


class ConversationMessage(BaseModel):
    """A single message in the conversation timeline."""

    role: MessageRole
    text: str = Field(min_length=1)
    created_at_iso: str


class ConversationState(BaseModel):
    """Serializable state for a conversation suitable for checkpointing."""

    conversation_id: str = Field(min_length=1)
    messages: list[ConversationMessage] = Field(default_factory=list)
    routed_domain: str | None = None
    processed_event_ids: list[str] = Field(default_factory=list)
    customer_id: str | None = None
    last_order_id: str | None = None
    last_tracking_id: str | None = None
    customer_memory: dict[str, str] = Field(default_factory=dict)
    customer_name: str | None = None
    requested_booking_date: str | None = None
    requested_booking_start_time: str | None = None
    requested_booking_end_time: str | None = None
    last_booking_id: str | None = None

def _max_messages() -> int:
    """Return the maximum number of messages to keep in memory."""
    raw = os.getenv("AI_ASSISTANTS_MAX_MESSAGES", "200")
    try:
        value = int(raw)
    except ValueError:
        return 200
    return value if value > 0 else 200


def _max_processed_events() -> int:
    """Return the maximum number of processed event ids to keep for idempotency."""
    raw = os.getenv("AI_ASSISTANTS_MAX_PROCESSED_EVENTS", "5000")
    try:
        value = int(raw)
    except ValueError:
        return 5000
    return value if value > 0 else 5000


def now_iso() -> str:
    """Return the current UTC timestamp as an ISO-8601 string."""
    return datetime.now(tz=timezone.utc).isoformat()


def append_message(
    state: ConversationState, *, role: MessageRole, text: str
) -> ConversationState:
    """Append a message to the state and return the updated state."""
    new_messages = [
        *state.messages,
        ConversationMessage(role=role, text=text, created_at_iso=now_iso()),
    ]
    max_messages = _max_messages()
    if len(new_messages) > max_messages:
        new_messages = new_messages[-max_messages:]
    return state.model_copy(update={"messages": new_messages})


def is_event_processed(state: ConversationState, event_id: str) -> bool:
    """Return true if the event id was already processed for this conversation."""
    return event_id in state.processed_event_ids


def mark_event_processed(state: ConversationState, event_id: str) -> ConversationState:
    """Mark an event id as processed and return the updated state."""
    if event_id in state.processed_event_ids:
        return state
    max_events = _max_processed_events()
    updated = [*state.processed_event_ids, event_id]
    if len(updated) > max_events:
        updated = updated[-max_events:]
    return state.model_copy(update={"processed_event_ids": updated})


def get_last_assistant_text(state: ConversationState) -> str | None:
    """Return the last assistant message text if present."""
    for message in reversed(state.messages):
        if message.role == MessageRole.assistant:
            return message.text
    return None


