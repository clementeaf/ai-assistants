from __future__ import annotations

from pathlib import Path

from ai_assistants.memory.vector_store import SqliteVectorMemoryStore, SqliteVectorMemoryConfig


def test_vector_memory_store_search_returns_best_match(tmp_path: Path) -> None:
    store = SqliteVectorMemoryStore(SqliteVectorMemoryConfig(path=tmp_path / "vec.sqlite3"))
    project_id = "proj"
    customer_id = "cust"

    store.add(project_id=project_id, customer_id=customer_id, text="pizza", embedding=[1.0, 0.0])
    store.add(project_id=project_id, customer_id=customer_id, text="envio", embedding=[0.0, 1.0])

    results = store.search(project_id=project_id, customer_id=customer_id, query_embedding=[1.0, 0.0], k=1)
    assert len(results) == 1
    item, score = results[0]
    assert item.text == "pizza"
    assert score > 0.9


