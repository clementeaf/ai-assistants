from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from ai_assistants.persistence.sqlite_memory_store import SqliteCustomerMemoryStore, SqliteMemoryStoreConfig


def test_memory_ttl_expires_last_ids(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AI_ASSISTANTS_MEMORY_TTL_SECONDS_LAST_IDS", "1")
    now = datetime(2025, 1, 1, 0, 0, 2, tzinfo=timezone.utc)
    store = SqliteCustomerMemoryStore(SqliteMemoryStoreConfig(path=tmp_path / "mem.sqlite3"), now_fn=lambda: now)

    # Insert memory at t=0
    old_ts = (now - timedelta(seconds=2)).isoformat()
    store.upsert(project_id="proj", customer_id="c1", data={"last_tracking_id": "TRACK-1"})
    # Manually backdate record updated_at_iso and per-key updated_at
    store._conn.execute(  # type: ignore[attr-defined]
        "UPDATE customer_memory SET memory_json = ?, updated_at_iso = ? WHERE project_id = ? AND customer_id = ?;",
        ('{"slots":{"last_tracking_id":"TRACK-1"},"updated_at":{"last_tracking_id":"' + old_ts + '"}}', old_ts, "proj", "c1"),
    )
    store._conn.commit()  # type: ignore[attr-defined]

    mem = store.get(project_id="proj", customer_id="c1")
    assert mem is not None
    assert "last_tracking_id" not in mem.data


