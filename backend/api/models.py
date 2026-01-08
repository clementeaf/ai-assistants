from __future__ import annotations

from pydantic import BaseModel, Field


class SendMessageRequest(BaseModel):
    """HTTP request body to send a user message into a conversation."""

    text: str = Field(min_length=1)

class WhatsAppInboundRequest(BaseModel):
    """Provider-agnostic WhatsApp inbound payload for local integration."""

    from_number: str = Field(min_length=1)
    text: str = Field(min_length=1)

class BaileysInboundRequest(BaseModel):
    """Inbound payload sent by a WhatsApp gateway service (deprecated alias name)."""

    message_id: str = Field(min_length=1)
    from_number: str = Field(min_length=1)
    text: str = Field(min_length=1)
    timestamp_iso: str = Field(min_length=1)


class SendMessageResponse(BaseModel):
    """HTTP response returned after running a conversation turn."""

    conversation_id: str
    response_text: str


class BaileysInboundResponse(BaseModel):
    """HTTP response consumed by a WhatsApp gateway service (deprecated alias name)."""

    conversation_id: str
    message_id: str
    response_text: str


class CreateJobResponse(BaseModel):
    """Response returned when scheduling an async job."""

    job_id: str


class JobStatusResponse(BaseModel):
    """Response returned when querying an async job."""

    job_id: str
    status: str
    conversation_id: str
    message_id: str | None
    response_text: str | None
    error_text: str | None


class CustomerMemoryResponse(BaseModel):
    """Response returning long-term memory for a customer."""

    customer_id: str
    memory: dict[str, str]


class WhatsAppGatewayInboundRequest(BaseModel):
    """Inbound payload sent by a WhatsApp gateway service (Baileys, custom, etc.)."""

    message_id: str = Field(min_length=1)
    from_number: str = Field(min_length=1)
    text: str = Field(min_length=1)
    timestamp_iso: str = Field(min_length=1)
    customer_id: str | None = None
    customer_name: str | None = None  # Nombre del perfil de WhatsApp


class WhatsAppGatewayInboundResponse(BaseModel):
    """HTTP response consumed by a WhatsApp gateway service to send the WhatsApp reply."""

    conversation_id: str
    message_id: str
    response_text: str


class WebSocketMessage(BaseModel):
    """WebSocket message format for chat communication."""

    type: str = Field(description="Message type: 'user_message', 'assistant_message', 'error', 'ping', 'pong'")
    text: str | None = Field(default=None, description="Message text content")
    conversation_id: str | None = Field(default=None, description="Conversation ID")
    error: str | None = Field(default=None, description="Error message if type is 'error'")
    timestamp: str | None = Field(default=None, description="ISO timestamp of the message")

