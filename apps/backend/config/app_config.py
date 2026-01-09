from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Application-level configuration."""

    enable_legacy_routes: bool
    max_messages: int
    max_processed_events: int
    thread_pool_workers: int


def load_app_config() -> AppConfig:
    """Load application configuration from environment variables."""
    legacy_routes_raw = os.getenv("AI_ASSISTANTS_ENABLE_LEGACY_ROUTES", "1").strip().lower()
    enable_legacy_routes = legacy_routes_raw not in {"0", "false", "no", "off"}

    max_messages_raw = os.getenv("AI_ASSISTANTS_MAX_MESSAGES", "200")
    try:
        max_messages = int(max_messages_raw)
    except ValueError:
        max_messages = 200
    max_messages = max_messages if max_messages > 0 else 200

    max_events_raw = os.getenv("AI_ASSISTANTS_MAX_PROCESSED_EVENTS", "5000")
    try:
        max_processed_events = int(max_events_raw)
    except ValueError:
        max_processed_events = 5000
    max_processed_events = max_processed_events if max_processed_events > 0 else 5000

    workers_raw = os.getenv("AI_ASSISTANTS_THREAD_POOL_WORKERS", "4")
    try:
        thread_pool_workers = int(workers_raw)
    except ValueError:
        thread_pool_workers = 4
    thread_pool_workers = max(1, thread_pool_workers)

    return AppConfig(
        enable_legacy_routes=enable_legacy_routes,
        max_messages=max_messages,
        max_processed_events=max_processed_events,
        thread_pool_workers=thread_pool_workers,
    )
