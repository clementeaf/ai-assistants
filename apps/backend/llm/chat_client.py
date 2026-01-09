from __future__ import annotations

from typing import Protocol


class ChatClient(Protocol):
    """Protocol for chat completion clients."""

    def chat_completion(self, *, system: str, user: str) -> str:  # pragma: no cover
        """Call chat completions and return the assistant content."""
        ...

