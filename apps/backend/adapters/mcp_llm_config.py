from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MCPLLMConfig:
    """Configuration for MCP LLM adapter."""

    server_url: str
    api_key: str | None
    timeout_seconds: float


def load_mcp_llm_config() -> MCPLLMConfig | None:
    """Load MCP LLM configuration from environment variables."""
    server_url = os.getenv("AI_ASSISTANTS_MCP_LLM_URL")
    if not server_url:
        return None

    api_key = os.getenv("AI_ASSISTANTS_MCP_LLM_API_KEY")
    timeout_raw = os.getenv("AI_ASSISTANTS_MCP_LLM_TIMEOUT_SECONDS", "30")
    try:
        timeout_seconds = float(timeout_raw)
    except ValueError:
        timeout_seconds = 30.0

    return MCPLLMConfig(
        server_url=server_url,
        api_key=api_key,
        timeout_seconds=timeout_seconds,
    )

