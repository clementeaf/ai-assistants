from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from ai_assistants.orchestrator.state import ConversationState
from ai_assistants.persistence.conversation_store import ConversationStore


@dataclass(frozen=True, slots=True)
class SqliteStoreConfig:
    """SQLite store configuration."""

    path: Path


def load_sqlite_store_config() -> SqliteStoreConfig:
    """Load sqlite store configuration from env vars."""
    raw = os.getenv("AI_ASSISTANTS_SQLITE_PATH", ".data/ai_assistants.sqlite3")
    return SqliteStoreConfig(path=Path(raw))


class SqliteConversationStore(ConversationStore):
    """SQLite-backed conversation store for persistence without external dependencies."""

    def __init__(self, config: SqliteStoreConfig) -> None:
        self._path = config.path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA synchronous=NORMAL;")
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
              conversation_id TEXT PRIMARY KEY,
              state_json TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

    def get(self, conversation_id: str) -> ConversationState | None:
        """Return state for the given conversation id if present."""
        cur = self._conn.execute(
            "SELECT state_json FROM conversations WHERE conversation_id = ?;",
            (conversation_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        state_json = row[0]
        try:
            payload = json.loads(state_json)
        except json.JSONDecodeError:
            return None
        return ConversationState.model_validate(payload)

    def put(self, state: ConversationState) -> None:
        """Persist the provided state in sqlite."""
        state_json = json.dumps(state.model_dump(mode="json"), ensure_ascii=False)
        self._conn.execute(
            """
            INSERT INTO conversations (conversation_id, state_json)
            VALUES (?, ?)
            ON CONFLICT(conversation_id) DO UPDATE SET state_json = excluded.state_json;
            """,
            (state.conversation_id, state_json),
        )
        self._conn.commit()


