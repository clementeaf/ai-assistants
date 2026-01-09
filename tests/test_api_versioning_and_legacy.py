from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ai_assistants.api.app import create_app


def _make_client(monkeypatch: pytest.MonkeyPatch, db_path: Path) -> TestClient:
    monkeypatch.setenv("AI_ASSISTANTS_SQLITE_PATH", str(db_path))
    monkeypatch.delenv("AI_ASSISTANTS_API_KEYS", raising=False)
    monkeypatch.delenv("AI_ASSISTANTS_RATE_LIMIT", raising=False)
    monkeypatch.delenv("WHATSAPP_WEBHOOK_SECRET", raising=False)
    monkeypatch.delenv("WHATSAPP_WEBHOOK_MAX_DRIFT_SECONDS", raising=False)
    return TestClient(create_app())


def test_legacy_routes_disabled(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AI_ASSISTANTS_ENABLE_LEGACY_ROUTES", "0")
    client = _make_client(monkeypatch, tmp_path / "db.sqlite3")

    # legacy route should not exist
    legacy_resp = client.post("/conversations/demo/messages", json={"text": "hola"})
    assert legacy_resp.status_code == 404

    # v1 route should exist (auth is disabled in dev mode)
    v1_resp = client.post("/v1/conversations/demo/messages", json={"text": "hola"})
    assert v1_resp.status_code == 200
    assert "response_text" in v1_resp.json()


def test_legacy_routes_enabled(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AI_ASSISTANTS_ENABLE_LEGACY_ROUTES", "1")
    client = _make_client(monkeypatch, tmp_path / "db.sqlite3")

    legacy_resp = client.post("/conversations/demo/messages", json={"text": "hola"})
    assert legacy_resp.status_code == 200
    assert "response_text" in legacy_resp.json()

