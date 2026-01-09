from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Channel(str, Enum):
    """Supported inbound channels."""

    web = "web"
    whatsapp = "whatsapp"


class InboundMessage(BaseModel):
    """Normalized inbound message, independent of the external provider payload."""

    channel: Channel
    sender_id: str = Field(min_length=1)
    text: str = Field(min_length=1)

    def conversation_id(self) -> str:
        """Create a stable conversation id derived from channel + sender."""
        return f"{self.channel.value}:{self.sender_id}"


