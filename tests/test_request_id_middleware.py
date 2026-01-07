from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ai_assistants.api.app import create_app


def _make_client(monkeypatch: pytest.MonkeyPatch, db_path: Path) -> TestClient:
    monkeypatch.setenv("AI_ASSISTANTS_SQLITE_PATH", str(db_path))
    monkeypatch.setenv("AI_ASSISTANTS_ENABLE_LEGACY_ROUTES", "0")
    monkeypatch.delenv("AI_ASSISTANTS_API_KEYS", raising=False)
    monkeypatch.delenv("AI_ASSISTANTS_RATE_LIMIT", raising=False)
    return TestClient(create_app())


def test_v1_response_includes_request_id_header(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = _make_client(monkeypatch, tmp_path / "db.sqlite3")
    resp = client.post("/v1/conversations/demo/messages", json={"text": "hola"})
    assert resp.status_code == 200
    request_id = resp.headers.get("X-Request-Id")
    assert isinstance(request_id, str)
    assert request_id.strip() != ""


