from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MCPBookingLogConfig:
    """Configuration for MCP booking log adapter."""

    server_url: str
    api_key: str | None
    timeout_seconds: float


def load_mcp_booking_log_config() -> MCPBookingLogConfig | None:
    """Load MCP booking log configuration from environment variables."""
    server_url = os.getenv("AI_ASSISTANTS_MCP_BOOKING_LOG_URL")
    if not server_url:
        return None

    api_key = os.getenv("AI_ASSISTANTS_MCP_BOOKING_LOG_API_KEY")
    timeout_raw = os.getenv("AI_ASSISTANTS_MCP_BOOKING_LOG_TIMEOUT_SECONDS", "10")
    try:
        timeout_seconds = float(timeout_raw)
    except ValueError:
        timeout_seconds = 10.0

    return MCPBookingLogConfig(
        server_url=server_url,
        api_key=api_key,
        timeout_seconds=timeout_seconds,
    )

