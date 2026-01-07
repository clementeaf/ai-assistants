from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ai_assistants.api.app import create_app


def _make_client(monkeypatch: pytest.MonkeyPatch, db_path: Path) -> TestClient:
    monkeypatch.setenv("AI_ASSISTANTS_SQLITE_PATH", str(db_path))
    monkeypatch.setenv("AI_ASSISTANTS_ENABLE_LEGACY_ROUTES", "0")
    monkeypatch.setenv("AI_ASSISTANTS_API_KEYS", "proj1:key1")
    monkeypatch.delenv("AI_ASSISTANTS_RATE_LIMIT", raising=False)
    monkeypatch.delenv("AI_ASSISTANTS_PURCHASES_HOOK_URL", raising=False)
    monkeypatch.delenv("AI_ASSISTANTS_PURCHASES_HOOK_API_KEY", raising=False)
    monkeypatch.delenv("AI_ASSISTANTS_PURCHASES_HOOK_SIGNATURE_SECRET", raising=False)
    monkeypatch.delenv("AI_ASSISTANTS_PURCHASES_HOOK_MAX_RETRIES", raising=False)
    monkeypatch.setenv("AI_ASSISTANTS_LLM_NLG_ENABLED", "0")
    return TestClient(create_app())


def test_memory_get_and_delete(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = _make_client(monkeypatch, tmp_path / "db.sqlite3")
    headers = {"X-API-Key": "key1", "X-Customer-Id": "+5491112345678"}

    # Run a turn to store memory
    msg = client.post(
        "/v1/channels/web/conversations/demo/messages",
        json={"text": "Seguimiento de ORDER-200"},
        headers=headers,
    )
    assert msg.status_code == 200

    got = client.get("/v1/memory", headers=headers)
    assert got.status_code == 200
    body = got.json()
    assert body["customer_id"] == "+5491112345678"
    assert body["memory"]["last_tracking_id"] == "TRACK-9002"

    deleted = client.delete("/v1/memory", headers=headers)
    assert deleted.status_code == 204

    got2 = client.get("/v1/memory", headers=headers)
    assert got2.status_code == 200
    assert got2.json()["memory"] == {}


