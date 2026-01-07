from __future__ import annotations

import json
import math
import os
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True, slots=True)
class VectorMemoryItem:
    """A single vector memory entry."""

    item_id: str
    project_id: str
    customer_id: str
    text: str
    embedding: list[float]
    created_at_iso: str


class EmbeddingsProvider(Protocol):
    """Protocol for embedding providers."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return embeddings for the provided texts."""


@dataclass(frozen=True, slots=True)
class SqliteVectorMemoryConfig:
    """SQLite vector memory configuration."""

    path: Path


def load_sqlite_vector_memory_config() -> SqliteVectorMemoryConfig:
    """Load sqlite vector memory configuration from env vars."""
    raw = os.getenv("AI_ASSISTANTS_SQLITE_PATH", ".data/ai_assistants.sqlite3")
    return SqliteVectorMemoryConfig(path=Path(raw))


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or len(a) == 0:
        return -1.0
    dot = 0.0
    na = 0.0
    nb = 0.0
    for i in range(len(a)):
        dot += a[i] * b[i]
        na += a[i] * a[i]
        nb += b[i] * b[i]
    if na == 0.0 or nb == 0.0:
        return -1.0
    return dot / (math.sqrt(na) * math.sqrt(nb))


class SqliteVectorMemoryStore:
    """SQLite-backed vector memory store (brute-force cosine over stored embeddings).

    Suitable for small/medium volumes. For large scale, swap for pgvector.
    """

    def __init__(self, config: SqliteVectorMemoryConfig) -> None:
        self._path = config.path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA synchronous=NORMAL;")
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS vector_memory (
              item_id TEXT PRIMARY KEY,
              project_id TEXT NOT NULL,
              customer_id TEXT NOT NULL,
              text TEXT NOT NULL,
              embedding_json TEXT NOT NULL,
              created_at_iso TEXT NOT NULL
            );
            """
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_vector_memory_scope ON vector_memory (project_id, customer_id);"
        )
        self._conn.commit()

    def add(
        self, *, project_id: str, customer_id: str, text: str, embedding: list[float]
    ) -> VectorMemoryItem:
        """Insert a memory item and return it."""
        item_id = str(uuid.uuid4())
        created_at = _now_iso()
        self._conn.execute(
            """
            INSERT INTO vector_memory (item_id, project_id, customer_id, text, embedding_json, created_at_iso)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (item_id, project_id, customer_id, text, json.dumps(embedding), created_at),
        )
        self._conn.commit()
        return VectorMemoryItem(
            item_id=item_id,
            project_id=project_id,
            customer_id=customer_id,
            text=text,
            embedding=embedding,
            created_at_iso=created_at,
        )

    def search(
        self,
        *,
        project_id: str,
        customer_id: str,
        query_embedding: list[float],
        k: int,
    ) -> list[tuple[VectorMemoryItem, float]]:
        """Return top-k items by cosine similarity."""
        cur = self._conn.execute(
            """
            SELECT item_id, text, embedding_json, created_at_iso
            FROM vector_memory
            WHERE project_id = ? AND customer_id = ?;
            """,
            (project_id, customer_id),
        )
        scored: list[tuple[VectorMemoryItem, float]] = []
        for item_id, text, embedding_json, created_at_iso in cur.fetchall():
            try:
                emb = json.loads(embedding_json)
            except json.JSONDecodeError:
                continue
            if not isinstance(emb, list) or any(not isinstance(x, (int, float)) for x in emb):
                continue
            emb_f = [float(x) for x in emb]
            score = _cosine_similarity(query_embedding, emb_f)
            scored.append(
                (
                    VectorMemoryItem(
                        item_id=item_id,
                        project_id=project_id,
                        customer_id=customer_id,
                        text=text,
                        embedding=emb_f,
                        created_at_iso=created_at_iso,
                    ),
                    score,
                )
            )
        scored.sort(key=lambda t: t[1], reverse=True)
        return scored[: max(0, k)]


