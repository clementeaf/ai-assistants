from __future__ import annotations

import json
import time
from pathlib import Path

import httpx
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
    monkeypatch.setenv("AI_ASSISTANTS_JOB_CALLBACK_URL", "https://callback.example.test")
    monkeypatch.delenv("AI_ASSISTANTS_JOB_CALLBACK_API_KEY", raising=False)
    monkeypatch.delenv("AI_ASSISTANTS_JOB_CALLBACK_SIGNATURE_SECRET", raising=False)
    monkeypatch.setenv("AI_ASSISTANTS_JOB_CALLBACK_MAX_RETRIES", "0")
    monkeypatch.setenv("AI_ASSISTANTS_JOB_CALLBACK_TIMEOUT_SECONDS", "1")
    return TestClient(create_app())


def test_job_completion_triggers_callback(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    captured: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8"))
        captured.append(body)
        return httpx.Response(status_code=200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    original_client = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda *args, **kwargs: original_client(transport=transport))

    client = _make_client(monkeypatch, tmp_path / "db.sqlite3")
    resp = client.post("/v1/async/conversations/demo/messages", json={"text": "TRACK-9001"})
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    deadline = time.time() + 1.0
    while time.time() < deadline:
        status_resp = client.get(f"/v1/jobs/{job_id}")
        assert status_resp.status_code == 200
        data = status_resp.json()
        if data["status"] == "succeeded":
            break
        time.sleep(0.01)

    assert len(captured) == 1
    assert captured[0]["job_id"] == job_id
    assert captured[0]["status"] == "succeeded"


