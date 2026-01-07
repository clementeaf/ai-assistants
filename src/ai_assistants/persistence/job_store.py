from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class JobStatus(str, Enum):
    """Status for an async job."""

    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


@dataclass(frozen=True, slots=True)
class JobRecord:
    """A persisted async job record."""

    job_id: str
    status: JobStatus
    conversation_id: str
    message_id: str | None
    response_text: str | None
    error_text: str | None
    created_at_iso: str
    updated_at_iso: str


class JobStore:
    """Job store abstraction."""

    def create(self, *, job_id: str, conversation_id: str, message_id: str | None) -> JobRecord:
        """Create a new job in pending state."""
        raise NotImplementedError

    def get(self, job_id: str) -> JobRecord | None:
        """Fetch a job by id."""
        raise NotImplementedError

    def mark_running(self, job_id: str) -> None:
        """Set job status to running."""
        raise NotImplementedError

    def mark_succeeded(self, job_id: str, response_text: str) -> None:
        """Set job status to succeeded and store the response."""
        raise NotImplementedError

    def mark_failed(self, job_id: str, error_text: str) -> None:
        """Set job status to failed and store the error."""
        raise NotImplementedError


