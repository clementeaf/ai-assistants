from __future__ import annotations

import os
from dataclasses import dataclass

from fastapi import Header, HTTPException
from structlog.contextvars import bind_contextvars


@dataclass(frozen=True, slots=True)
class AuthContext:
    """Authentication context inferred from an API key."""

    project_id: str
    api_key: str


def _parse_api_keys(raw: str) -> dict[str, str]:
    """Parse API keys mapping from env.

    Format: "projectA:keyA,projectB:keyB"
    """
    mapping: dict[str, str] = {}
    for pair in [p.strip() for p in raw.split(",") if p.strip() != ""]:
        if ":" not in pair:
            continue
        project_id, api_key = pair.split(":", 1)
        project_id = project_id.strip()
        api_key = api_key.strip()
        if project_id == "" or api_key == "":
            continue
        mapping[project_id] = api_key
    return mapping


def _is_auth_enabled() -> bool:
    """Return true if auth is enabled by environment configuration."""
    raw = os.getenv("AI_ASSISTANTS_API_KEYS")
    return raw is not None and raw.strip() != ""


def require_auth(x_api_key: str | None = Header(default=None)) -> AuthContext:
    """FastAPI dependency enforcing API key authentication.

    If AI_ASSISTANTS_API_KEYS is not set, authentication is disabled (dev mode).
    """
    if not _is_auth_enabled():
        bind_contextvars(project_id="dev")
        return AuthContext(project_id="dev", api_key="dev")

    if x_api_key is None or x_api_key.strip() == "":
        raise HTTPException(status_code=401, detail="Missing X-API-Key")

    raw = os.getenv("AI_ASSISTANTS_API_KEYS", "")
    mapping = _parse_api_keys(raw)
    for project_id, expected_key in mapping.items():
        if x_api_key == expected_key:
            bind_contextvars(project_id=project_id)
            return AuthContext(project_id=project_id, api_key=x_api_key)

    raise HTTPException(status_code=401, detail="Invalid X-API-Key")


