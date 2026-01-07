from __future__ import annotations

from dataclasses import dataclass
from structlog.contextvars import get_contextvars

from ai_assistants.memory.embeddings import EmbeddingsProvider, build_embeddings_provider_from_env
from ai_assistants.memory.vector_store import SqliteVectorMemoryStore, load_sqlite_vector_memory_config


@dataclass(frozen=True, slots=True)
class RecallResult:
    """Recall result entry."""

    text: str
    score: float


class VectorMemoryTools:
    """Tooling for vector memory (remember/recall)."""

    def __init__(self, store: SqliteVectorMemoryStore, embeddings: EmbeddingsProvider | None) -> None:
        self._store = store
        self._embeddings = embeddings

    @classmethod
    def from_env(cls) -> "VectorMemoryTools":
        store = SqliteVectorMemoryStore(load_sqlite_vector_memory_config())
        embeddings = build_embeddings_provider_from_env()
        return cls(store=store, embeddings=embeddings)

    def remember(self, *, customer_id: str, text: str) -> None:
        """Store a text snippet into vector memory for later retrieval."""
        if self._embeddings is None:
            return
        ctx = get_contextvars()
        project_id = ctx.get("project_id")
        resolved_project_id = project_id if isinstance(project_id, str) and project_id.strip() != "" else "dev"
        emb = self._embeddings.embed([text])[0]
        self._store.add(project_id=resolved_project_id, customer_id=customer_id, text=text, embedding=emb)

    def recall(self, *, customer_id: str, query: str, k: int = 5) -> list[RecallResult]:
        """Retrieve the top-k most relevant memory snippets."""
        if self._embeddings is None:
            return []
        ctx = get_contextvars()
        project_id = ctx.get("project_id")
        resolved_project_id = project_id if isinstance(project_id, str) and project_id.strip() != "" else "dev"
        query_emb = self._embeddings.embed([query])[0]
        results = self._store.search(
            project_id=resolved_project_id, customer_id=customer_id, query_embedding=query_emb, k=k
        )
        return [RecallResult(text=item.text, score=score) for item, score in results]


