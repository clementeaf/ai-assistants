from __future__ import annotations

import os
import time
from dataclasses import dataclass

from fastapi import HTTPException


@dataclass(frozen=True, slots=True)
class RateLimitConfig:
    """Rate limiting configuration."""

    max_requests: int
    window_seconds: int


def load_rate_limit_config() -> RateLimitConfig | None:
    """Load rate limiting config from env vars.

    If not configured, returns None (disabled).
    """
    raw = os.getenv("AI_ASSISTANTS_RATE_LIMIT", "").strip()
    if raw == "":
        return None

    # Format: "60/60" => 60 req per 60 seconds
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


class InMemoryRateLimiter:
    """Simple fixed-window rate limiter keyed by string identifier."""

    def __init__(self, config: RateLimitConfig) -> None:
        self._config = config
        self._buckets: dict[str, tuple[int, int]] = {}

    def check(self, key: str) -> None:
        """Check and consume one request for the given key, or raise HTTP 429."""
        now = int(time.time())
        window_start = now - (now % self._config.window_seconds)

        count, current_window = self._buckets.get(key, (0, window_start))
        if current_window != window_start:
            count = 0
            current_window = window_start

        count += 1
        self._buckets[key] = (count, current_window)

        if count > self._config.max_requests:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")


