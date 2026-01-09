from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ai_assistants.api.app import create_app


def _make_client(monkeypatch: pytest.MonkeyPatch, db_path: Path) -> TestClient:
    monkeypatch.setenv("AI_ASSISTANTS_SQLITE_PATH", str(db_path))
    monkeypatch.setenv("AI_ASSISTANTS_ENABLE_LEGACY_ROUTES", "0")
    monkeypatch.delenv("WHATSAPP_WEBHOOK_SECRET", raising=False)
    monkeypatch.delenv("WHATSAPP_WEBHOOK_MAX_DRIFT_SECONDS", raising=False)
    return TestClient(create_app())


def test_v1_requires_api_key_when_configured(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AI_ASSISTANTS_API_KEYS", "proj1:key1")
    monkeypatch.delenv("AI_ASSISTANTS_RATE_LIMIT", raising=False)
    client = _make_client(monkeypatch, tmp_path / "db.sqlite3")

    missing = client.post("/v1/conversations/demo/messages", json={"text": "hola"})
    assert missing.status_code == 401

    invalid = client.post(
        "/v1/conversations/demo/messages",
        json={"text": "hola"},
        headers={"X-API-Key": "wrong"},
    )
    assert invalid.status_code == 401

    ok = client.post(
        "/v1/conversations/demo/messages",
        json={"text": "hola"},
        headers={"X-API-Key": "key1"},
    )
    assert ok.status_code == 200


def test_rate_limit_enforced_per_project(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AI_ASSISTANTS_API_KEYS", "proj1:key1")
    monkeypatch.setenv("AI_ASSISTANTS_RATE_LIMIT", "1/60")
    client = _make_client(monkeypatch, tmp_path / "db.sqlite3")

    first = client.post(
        "/v1/conversations/demo/messages",
        json={"text": "hola"},
        headers={"X-API-Key": "key1"},
    )
    assert first.status_code == 200

    second = client.post(
        "/v1/conversations/demo/messages",
        json={"text": "hola"},
        headers={"X-API-Key": "key1"},
    )
    assert second.status_code == 429

