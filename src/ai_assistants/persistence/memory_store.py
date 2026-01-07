from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CustomerMemory:
    """Long-term memory stored per customer and project."""

    project_id: str
    customer_id: str
    data: dict[str, str]
    updated_at_iso: str


class CustomerMemoryStore:
    """Long-term memory store abstraction."""

    def get(self, *, project_id: str, customer_id: str) -> CustomerMemory | None:
        """Fetch memory for a customer."""
        raise NotImplementedError

    def upsert(self, *, project_id: str, customer_id: str, data: dict[str, str]) -> CustomerMemory:
        """Replace memory data for a customer and return updated record."""
        raise NotImplementedError

    def delete(self, *, project_id: str, customer_id: str) -> None:
        """Delete memory for a customer (forget)."""
        raise NotImplementedError


