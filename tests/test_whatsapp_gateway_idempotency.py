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
    monkeypatch.delenv("WHATSAPP_WEBHOOK_SECRET", raising=False)
    monkeypatch.delenv("WHATSAPP_WEBHOOK_MAX_DRIFT_SECONDS", raising=False)
    return TestClient(create_app())


def test_gateway_idempotency_by_message_id(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = _make_client(monkeypatch, tmp_path / "db.sqlite3")

    payload = {
        "message_id": "m1",
        "from_number": "+5491112345678",
        "text": "Revisar compra ORDER-100",
        "timestamp_iso": "2025-12-18T12:00:00Z",
    }
    first = client.post("/v1/channels/whatsapp/gateway/inbound", json=payload)
    assert first.status_code == 200
    first_json = first.json()
    assert first_json["message_id"] == "m1"

    second = client.post("/v1/channels/whatsapp/gateway/inbound", json=payload)
    assert second.status_code == 200
    second_json = second.json()

    # second call should return the cached last assistant response
    assert second_json["message_id"] == "m1"
    assert second_json["conversation_id"] == first_json["conversation_id"]
    assert second_json["response_text"] == first_json["response_text"]


