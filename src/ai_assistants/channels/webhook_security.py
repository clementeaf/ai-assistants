from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WebhookSecurityConfig:
    """Configuration for webhook signature verification."""

    secret: str
    max_timestamp_drift_seconds: int


def load_webhook_security_config() -> WebhookSecurityConfig | None:
    """Load webhook verification config from env vars.

    If no secret is configured, verification is disabled and this returns None.
    """
    secret = os.getenv("WHATSAPP_WEBHOOK_SECRET")
    if secret is None or secret.strip() == "":
        return None
    drift_raw = os.getenv("WHATSAPP_WEBHOOK_MAX_DRIFT_SECONDS", "300")
    try:
        drift = int(drift_raw)
    except ValueError:
        drift = 300
    return WebhookSecurityConfig(secret=secret, max_timestamp_drift_seconds=drift)


def compute_signature(secret: str, timestamp: str, body_bytes: bytes) -> str:
    """Compute the expected signature for a timestamp + raw body."""
    signing_input = timestamp.encode("utf-8") + b"." + body_bytes
    digest = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def verify_signature(
    *, config: WebhookSecurityConfig, timestamp: str, signature: str, body_bytes: bytes
) -> bool:
    """Verify webhook signature and timestamp drift."""
    try:
        ts_int = int(timestamp)
    except ValueError:
        return False

    now = int(time.time())
    if abs(now - ts_int) > config.max_timestamp_drift_seconds:
        return False

    expected = compute_signature(config.secret, timestamp, body_bytes)
    return hmac.compare_digest(expected, signature)


