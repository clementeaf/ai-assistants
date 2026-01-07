from __future__ import annotations

import time
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


def _poll_job(client: TestClient, job_id: str, timeout_seconds: float = 1.0) -> dict[str, object]:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        resp = client.get(f"/v1/jobs/{job_id}")
        assert resp.status_code == 200
        data = resp.json()
        if data["status"] in ("succeeded", "failed"):
            return data
        time.sleep(0.01)
    raise AssertionError("Job did not complete before timeout")


def test_async_web_job(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = _make_client(monkeypatch, tmp_path / "db.sqlite3")
    resp = client.post("/v1/async/conversations/demo/messages", json={"text": "TRACK-9001"})
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]
    assert isinstance(job_id, str) and job_id.strip() != ""

    job = _poll_job(client, job_id)
    assert job["status"] == "succeeded"
    assert isinstance(job["response_text"], str)
    assert "Tracking" in job["response_text"]


def test_async_whatsapp_gateway_job(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    client = _make_client(monkeypatch, tmp_path / "db.sqlite3")
    resp = client.post(
        "/v1/async/channels/whatsapp/gateway/inbound",
        json={
            "message_id": "m-async-1",
            "from_number": "+5491112345678",
            "text": "mis compras",
            "timestamp_iso": "2025-12-18T12:00:00Z",
        },
    )
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    job = _poll_job(client, job_id)
    assert job["status"] == "succeeded"
    assert isinstance(job["response_text"], str)
    assert "compras recientes" in job["response_text"]


