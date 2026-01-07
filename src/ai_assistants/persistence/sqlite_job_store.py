from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from ai_assistants.orchestrator.state import now_iso
from ai_assistants.persistence.job_store import JobRecord, JobStatus, JobStore


@dataclass(frozen=True, slots=True)
class SqliteJobStoreConfig:
    """SQLite job store configuration."""

    path: Path


def load_sqlite_job_store_config() -> SqliteJobStoreConfig:
    """Load sqlite job store configuration from env vars.

    Uses the same default path as the conversation store.
    """
    raw = os.getenv("AI_ASSISTANTS_SQLITE_PATH", ".data/ai_assistants.sqlite3")
    return SqliteJobStoreConfig(path=Path(raw))


class SqliteJobStore(JobStore):
    """SQLite-backed job store."""

    def __init__(self, config: SqliteJobStoreConfig) -> None:
        self._path = config.path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA synchronous=NORMAL;")
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
              job_id TEXT PRIMARY KEY,
              status TEXT NOT NULL,
              conversation_id TEXT NOT NULL,
              message_id TEXT,
              response_text TEXT,
              error_text TEXT,
              created_at_iso TEXT NOT NULL,
              updated_at_iso TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

    def create(self, *, job_id: str, conversation_id: str, message_id: str | None) -> JobRecord:
        """Create a new job in pending state."""
        ts = now_iso()
        self._conn.execute(
            """
            INSERT INTO jobs (job_id, status, conversation_id, message_id, response_text, error_text, created_at_iso, updated_at_iso)
            VALUES (?, ?, ?, ?, NULL, NULL, ?, ?);
            """,
            (job_id, JobStatus.pending.value, conversation_id, message_id, ts, ts),
        )
        self._conn.commit()
        return JobRecord(
            job_id=job_id,
            status=JobStatus.pending,
            conversation_id=conversation_id,
            message_id=message_id,
            response_text=None,
            error_text=None,
            created_at_iso=ts,
            updated_at_iso=ts,
        )

    def get(self, job_id: str) -> JobRecord | None:
        """Fetch a job by id."""
        cur = self._conn.execute(
            """
            SELECT job_id, status, conversation_id, message_id, response_text, error_text, created_at_iso, updated_at_iso
            FROM jobs
            WHERE job_id = ?;
            """,
            (job_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        status = JobStatus(row[1])
        return JobRecord(
            job_id=row[0],
            status=status,
            conversation_id=row[2],
            message_id=row[3],
            response_text=row[4],
            error_text=row[5],
            created_at_iso=row[6],
            updated_at_iso=row[7],
        )

    def mark_running(self, job_id: str) -> None:
        """Set job status to running."""
        ts = now_iso()
        self._conn.execute(
            "UPDATE jobs SET status = ?, updated_at_iso = ? WHERE job_id = ?;",
            (JobStatus.running.value, ts, job_id),
        )
        self._conn.commit()

    def mark_succeeded(self, job_id: str, response_text: str) -> None:
        """Set job status to succeeded and store the response."""
        ts = now_iso()
        self._conn.execute(
            """
            UPDATE jobs
            SET status = ?, response_text = ?, error_text = NULL, updated_at_iso = ?
            WHERE job_id = ?;
            """,
            (JobStatus.succeeded.value, response_text, ts, job_id),
        )
        self._conn.commit()

    def mark_failed(self, job_id: str, error_text: str) -> None:
        """Set job status to failed and store the error."""
        ts = now_iso()
        self._conn.execute(
            """
            UPDATE jobs
            SET status = ?, error_text = ?, updated_at_iso = ?
            WHERE job_id = ?;
            """,
            (JobStatus.failed.value, error_text, ts, job_id),
        )
        self._conn.commit()


