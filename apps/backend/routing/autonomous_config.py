from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AutonomousConfig:
    """Configuration for autonomous LLM mode."""

    enabled: bool
    max_history_messages: int


def load_autonomous_config() -> AutonomousConfig:
    """Load autonomous mode configuration from environment variables."""
    enabled_raw = os.getenv("AI_ASSISTANTS_AUTONOMOUS_ENABLED", "0").strip().lower()
    enabled = enabled_raw in {"1", "true", "yes", "on"}

    max_history_raw = os.getenv("AI_ASSISTANTS_AUTONOMOUS_MAX_HISTORY", "10")
    try:
        max_history_messages = int(max_history_raw)
    except ValueError:
        max_history_messages = 10
    max_history_messages = max(1, min(max_history_messages, 50))

    return AutonomousConfig(enabled=enabled, max_history_messages=max_history_messages)
