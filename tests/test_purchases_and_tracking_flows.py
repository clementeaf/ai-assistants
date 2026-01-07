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


def test_tracking_by_order_id_in_gateway(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = _make_client(monkeypatch, tmp_path / "db.sqlite3")
    payload = {
        "message_id": "m-track-order",
        "from_number": "+5491112345678",
        "text": "Seguimiento de ORDER-200",
        "timestamp_iso": "2025-12-18T12:00:00Z",
    }
    resp = client.post("/v1/channels/whatsapp/gateway/inbound", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["message_id"] == "m-track-order"
    assert "Orden ORDER-200" in data["response_text"]
    assert "Tracking TRACK-9002" in data["response_text"]


def test_tracking_by_tracking_id_in_gateway(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = _make_client(monkeypatch, tmp_path / "db.sqlite3")
    payload = {
        "message_id": "m-track-id",
        "from_number": "+5491112345678",
        "text": "TRACK-9001",
        "timestamp_iso": "2025-12-18T12:00:00Z",
    }
    resp = client.post("/v1/channels/whatsapp/gateway/inbound", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "Tracking TRACK-9001" in data["response_text"]


def test_list_orders_in_gateway(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = _make_client(monkeypatch, tmp_path / "db.sqlite3")
    payload = {
        "message_id": "m-list",
        "from_number": "+5491112345678",
        "text": "mis compras",
        "timestamp_iso": "2025-12-18T12:00:00Z",
    }
    resp = client.post("/v1/channels/whatsapp/gateway/inbound", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "Estas son tus compras recientes" in data["response_text"]
    assert "ORDER-100" in data["response_text"]


