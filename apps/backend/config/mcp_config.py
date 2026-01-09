from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MCPCalendarConfig:
    """MCP Calendar server configuration."""

    server_url: str
    api_key: str | None
    timeout_seconds: float


@dataclass(frozen=True, slots=True)
class MCPProfessionalsConfig:
    """MCP Professionals server configuration."""

    server_url: str
    api_key: str | None
    timeout_seconds: float


@dataclass(frozen=True, slots=True)
class MCPBookingLogConfig:
    """MCP Booking Log server configuration."""

    server_url: str
    api_key: str | None
    timeout_seconds: float


@dataclass(frozen=True, slots=True)
class MCPLLMConfig:
    """MCP LLM server configuration."""

    server_url: str
    api_key: str | None
    timeout_seconds: float


@dataclass(frozen=True, slots=True)
class MCPConfig:
    """All MCP server configurations."""

    calendar: MCPCalendarConfig | None
    professionals: MCPProfessionalsConfig | None
    booking_log: MCPBookingLogConfig | None
    llm: MCPLLMConfig | None
    booking_flow_server_url: str


def _load_mcp_calendar_config() -> MCPCalendarConfig | None:
    """Load MCP Calendar configuration."""
    server_url = os.getenv("AI_ASSISTANTS_MCP_CALENDAR_URL")
    if not server_url:
        return None

    api_key = os.getenv("AI_ASSISTANTS_MCP_CALENDAR_API_KEY")
    timeout_raw = os.getenv("AI_ASSISTANTS_MCP_CALENDAR_TIMEOUT_SECONDS", "30")
    try:
        timeout_seconds = float(timeout_raw)
    except ValueError:
        timeout_seconds = 30.0
    timeout_seconds = max(1.0, timeout_seconds)

    return MCPCalendarConfig(server_url=server_url, api_key=api_key, timeout_seconds=timeout_seconds)


def _load_mcp_professionals_config() -> MCPProfessionalsConfig | None:
    """Load MCP Professionals configuration."""
    server_url = os.getenv("AI_ASSISTANTS_MCP_PROFESSIONALS_URL")
    if not server_url:
        return None

    api_key = os.getenv("AI_ASSISTANTS_MCP_PROFESSIONALS_API_KEY")
    timeout_raw = os.getenv("AI_ASSISTANTS_MCP_PROFESSIONALS_TIMEOUT_SECONDS", "30")
    try:
        timeout_seconds = float(timeout_raw)
    except ValueError:
        timeout_seconds = 30.0
    timeout_seconds = max(1.0, timeout_seconds)

    return MCPProfessionalsConfig(server_url=server_url, api_key=api_key, timeout_seconds=timeout_seconds)


def _load_mcp_booking_log_config() -> MCPBookingLogConfig | None:
    """Load MCP Booking Log configuration."""
    server_url = os.getenv("AI_ASSISTANTS_MCP_BOOKING_LOG_URL")
    if not server_url:
        return None

    api_key = os.getenv("AI_ASSISTANTS_MCP_BOOKING_LOG_API_KEY")
    timeout_raw = os.getenv("AI_ASSISTANTS_MCP_BOOKING_LOG_TIMEOUT_SECONDS", "30")
    try:
        timeout_seconds = float(timeout_raw)
    except ValueError:
        timeout_seconds = 30.0
    timeout_seconds = max(1.0, timeout_seconds)

    return MCPBookingLogConfig(server_url=server_url, api_key=api_key, timeout_seconds=timeout_seconds)


def _load_mcp_llm_config() -> MCPLLMConfig | None:
    """Load MCP LLM configuration."""
    server_url = os.getenv("AI_ASSISTANTS_MCP_LLM_URL")
    if not server_url:
        return None

    api_key = os.getenv("AI_ASSISTANTS_MCP_LLM_API_KEY")
    timeout_raw = os.getenv("AI_ASSISTANTS_MCP_LLM_TIMEOUT_SECONDS", "30")
    try:
        timeout_seconds = float(timeout_raw)
    except ValueError:
        timeout_seconds = 30.0
    timeout_seconds = max(1.0, timeout_seconds)

    return MCPLLMConfig(server_url=server_url, api_key=api_key, timeout_seconds=timeout_seconds)


def load_mcp_config() -> MCPConfig:
    """Load all MCP server configurations."""
    booking_flow_url = os.getenv("BOOKING_FLOW_SERVER_URL", "http://localhost:60006")

    return MCPConfig(
        calendar=_load_mcp_calendar_config(),
        professionals=_load_mcp_professionals_config(),
        booking_log=_load_mcp_booking_log_config(),
        llm=_load_mcp_llm_config(),
        booking_flow_server_url=booking_flow_url,
    )
