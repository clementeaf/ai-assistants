from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from ai_assistants.orchestrator.state import now_iso
from ai_assistants.persistence.memory_store import CustomerMemory, CustomerMemoryStore


@dataclass(frozen=True, slots=True)
class SqliteMemoryStoreConfig:
    """SQLite memory store configuration."""

    path: Path


def load_sqlite_memory_store_config() -> SqliteMemoryStoreConfig:
    """Load sqlite memory store configuration from env vars.

    Uses the same default path as the conversation store.
    """
    raw = os.getenv("AI_ASSISTANTS_SQLITE_PATH", ".data/ai_assistants.sqlite3")
    return SqliteMemoryStoreConfig(path=Path(raw))

def _ttl_seconds_last_ids() -> int:
    raw = os.getenv("AI_ASSISTANTS_MEMORY_TTL_SECONDS_LAST_IDS", str(60 * 60 * 24 * 30))
    try:
        value = int(raw)
    except ValueError:
        return 60 * 60 * 24 * 30
    return value if value > 0 else 60 * 60 * 24 * 30


def _parse_iso(ts: str) -> datetime | None:
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def _is_expired(updated_at_iso: str, now: datetime, ttl_seconds: int) -> bool:
    parsed = _parse_iso(updated_at_iso)
    if parsed is None:
        return True
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return (now - parsed).total_seconds() > ttl_seconds


class SqliteCustomerMemoryStore(CustomerMemoryStore):
    """SQLite-backed long-term customer memory store."""

    def __init__(self, config: SqliteMemoryStoreConfig, now_fn: Callable[[], datetime] | None = None) -> None:
        self._path = config.path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA synchronous=NORMAL;")
        self._init_schema()
        self._now_fn = now_fn or (lambda: datetime.now(tz=timezone.utc))

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS customer_memory (
              project_id TEXT NOT NULL,
              customer_id TEXT NOT NULL,
              memory_json TEXT NOT NULL,
              updated_at_iso TEXT NOT NULL,
              PRIMARY KEY (project_id, customer_id)
            );
            """
        )
        self._conn.commit()

    def get(self, *, project_id: str, customer_id: str) -> CustomerMemory | None:
        """Fetch memory for a customer."""
        cur = self._conn.execute(
            """
            SELECT memory_json, updated_at_iso
            FROM customer_memory
            WHERE project_id = ? AND customer_id = ?;
            """,
            (project_id, customer_id),
        )
        row = cur.fetchone()
        if row is None:
            return None
        memory_json = row[0]
        updated_at_iso = row[1]

        try:
            parsed = json.loads(memory_json)
        except json.JSONDecodeError:
            parsed = {}

        slots: dict[str, str] = {}
        per_key_updated: dict[str, str] = {}
        if isinstance(parsed, dict) and "slots" in parsed and "updated_at" in parsed:
            raw_slots = parsed.get("slots")
            raw_updated = parsed.get("updated_at")
            if isinstance(raw_slots, dict):
                slots = {str(k): str(v) for k, v in raw_slots.items()}
            if isinstance(raw_updated, dict):
                per_key_updated = {str(k): str(v) for k, v in raw_updated.items()}
        elif isinstance(parsed, dict):
            slots = {str(k): str(v) for k, v in parsed.items()}
            per_key_updated = {key: updated_at_iso for key in slots.keys()}

        # TTL enforcement for last ids
        ttl_seconds = _ttl_seconds_last_ids()
        now = self._now_fn()
        for key in ("last_order_id", "last_tracking_id"):
            if key in slots:
                key_ts = per_key_updated.get(key, updated_at_iso)
                if _is_expired(key_ts, now, ttl_seconds):
                    slots.pop(key, None)

        return CustomerMemory(project_id=project_id, customer_id=customer_id, data=slots, updated_at_iso=updated_at_iso)

    def upsert(self, *, project_id: str, customer_id: str, data: dict[str, str]) -> CustomerMemory:
        """Replace memory data for a customer and return updated record."""
        ts = now_iso()
        body = {"slots": data, "updated_at": {k: ts for k in data.keys()}}
        memory_json = json.dumps(body, ensure_ascii=False)
        self._conn.execute(
            """
            INSERT INTO customer_memory (project_id, customer_id, memory_json, updated_at_iso)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(project_id, customer_id) DO UPDATE
            SET memory_json = excluded.memory_json,
                updated_at_iso = excluded.updated_at_iso;
            """,
            (project_id, customer_id, memory_json, ts),
        )
        self._conn.commit()
        return CustomerMemory(project_id=project_id, customer_id=customer_id, data=data, updated_at_iso=ts)

    def delete(self, *, project_id: str, customer_id: str) -> None:
        """Delete memory for a customer (forget)."""
        self._conn.execute(
            "DELETE FROM customer_memory WHERE project_id = ? AND customer_id = ?;",
            (project_id, customer_id),
        )
        self._conn.commit()


