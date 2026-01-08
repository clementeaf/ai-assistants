from __future__ import annotations

from typing import Any

import httpx

from ai_assistants.llm.chat_client import ChatClient


class MCPLLMAdapter(ChatClient):
    """Adapter that connects to an LLM service via MCP (Model Context Protocol)."""

    def __init__(self, mcp_server_url: str, api_key: str | None = None, timeout_seconds: float = 30.0) -> None:
        self._mcp_url = mcp_server_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout_seconds
        self._client = httpx.Client(timeout=timeout_seconds)

    def _call_mcp_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call an MCP tool and return the result."""
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
        }

        response = self._client.post(
            f"{self._mcp_url}/mcp",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        json_response = response.json()
        if "error" in json_response and json_response["error"] is not None:
            error_msg = json_response["error"].get("message", "Unknown error")
            raise ValueError(f"MCP error: {error_msg}")
        return json_response.get("result", {})

    def chat_completion(self, *, system: str, user: str) -> str:
        """Call the chat completions endpoint and return the assistant content."""
        result = self._call_mcp_tool(
            "chat_completion",
            {
                "system": system,
                "user": user,
            },
        )
        content = result.get("content")
        if not isinstance(content, str):
            raise ValueError("Invalid MCP LLM response: missing content")
        return content

