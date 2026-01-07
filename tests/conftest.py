from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ai_assistants.api.app import create_app


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Create a FastAPI test client with isolated sqlite storage and env vars."""
    db_path = tmp_path / "test.sqlite3"
    monkeypatch.setenv("AI_ASSISTANTS_SQLITE_PATH", str(db_path))
    monkeypatch.delenv("AI_ASSISTANTS_API_KEYS", raising=False)
    monkeypatch.delenv("AI_ASSISTANTS_RATE_LIMIT", raising=False)
    monkeypatch.setenv("AI_ASSISTANTS_ENABLE_LEGACY_ROUTES", "1")
    monkeypatch.delenv("WHATSAPP_WEBHOOK_SECRET", raising=False)
    monkeypatch.delenv("WHATSAPP_WEBHOOK_MAX_DRIFT_SECONDS", raising=False)

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


