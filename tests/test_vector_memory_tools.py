from __future__ import annotations

from pathlib import Path

from structlog.contextvars import bind_contextvars, clear_contextvars

from ai_assistants.memory.vector_store import SqliteVectorMemoryStore, SqliteVectorMemoryConfig
from ai_assistants.tools.vector_memory_tools import VectorMemoryTools


class FakeEmbeddings:
    def embed(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for text in texts:
            # Very small deterministic embedding: [contains_pizza, contains_envio]
            t = text.lower()
            out.append([1.0 if "pizza" in t else 0.0, 1.0 if "envio" in t else 0.0])
        return out


def test_vector_memory_tools_remember_and_recall(tmp_path: Path) -> None:
    store = SqliteVectorMemoryStore(SqliteVectorMemoryConfig(path=tmp_path / "vec.sqlite3"))
    tools = VectorMemoryTools(store=store, embeddings=FakeEmbeddings())

    bind_contextvars(project_id="proj1")
    try:
        tools.remember(customer_id="c1", text="Me gusta la pizza")
        tools.remember(customer_id="c1", text="Quiero saber el envio")
        results = tools.recall(customer_id="c1", query="pizza", k=2)
        assert len(results) >= 1
        assert "pizza" in results[0].text.lower()
    finally:
        clear_contextvars()


