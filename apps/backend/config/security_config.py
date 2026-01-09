from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RateLimitConfig:
    """Rate limiting configuration."""

    max_requests: int
    window_seconds: int


@dataclass(frozen=True, slots=True)
class WebhookSecurityConfig:
    """Webhook security configuration."""

    secret: str
    algorithm: str


@dataclass(frozen=True, slots=True)
class SecurityConfig:
    """Security configuration including auth, rate limiting, and webhooks."""

    api_keys: dict[str, str]
    rate_limit: RateLimitConfig | None
    webhook_secret: str | None


def _parse_api_keys(raw: str) -> dict[str, str]:
    """Parse API keys mapping from environment variable.

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


def _load_rate_limit_config() -> RateLimitConfig | None:
    """Load rate limiting configuration."""
    raw = os.getenv("AI_ASSISTANTS_RATE_LIMIT", "").strip()
    if raw == "":
        return None

    if "/" not in raw:
        return None
    max_req_raw, window_raw = raw.split("/", 1)
    try:
        max_requests = int(max_req_raw)
        window_seconds = int(window_raw)
    except ValueError:
        return None

    if max_requests <= 0 or window_seconds <= 0:
        return None
    return RateLimitConfig(max_requests=max_requests, window_seconds=window_seconds)


def load_security_config() -> SecurityConfig:
    """Load security configuration from environment variables."""
    api_keys_raw = os.getenv("AI_ASSISTANTS_API_KEYS", "")
    api_keys = _parse_api_keys(api_keys_raw) if api_keys_raw.strip() != "" else {}

    webhook_secret = os.getenv("WHATSAPP_WEBHOOK_SECRET")

    return SecurityConfig(
        api_keys=api_keys,
        rate_limit=_load_rate_limit_config(),
        webhook_secret=webhook_secret,
    )
