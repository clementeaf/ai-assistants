#!/usr/bin/env python3
"""MCP LLM Server - LLM service via Model Context Protocol."""

from __future__ import annotations

import os
import time
from collections.abc import Mapping
from typing import Any

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="MCP LLM Server", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LLM_BASE_URL = os.getenv("LLM_MCP_BASE_URL", "https://api.openai.com/v1")
LLM_API_KEY = os.getenv("LLM_MCP_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MCP_MODEL", "gpt-4o-mini")
LLM_TIMEOUT = float(os.getenv("LLM_MCP_TIMEOUT_SECONDS", "30"))
LLM_TEMPERATURE = float(os.getenv("LLM_MCP_TEMPERATURE", "0"))


class MCPRequest(BaseModel):
    """MCP JSON-RPC request."""

    jsonrpc: str = "2.0"
    id: int | str
    method: str
    params: dict


class MCPResponse(BaseModel):
    """MCP JSON-RPC response."""

    jsonrpc: str = "2.0"
    id: int | str
    result: dict | None = None
    error: dict | None = None


class LLMClient:
    """Client for OpenAI-compatible LLM APIs."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float,
        temperature: float,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout = timeout
        self._temperature = temperature
        self._client = httpx.Client(timeout=timeout)

    def chat_completion(
        self,
        *,
        system: str,
        user: str,
        temperature: float | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        """Call chat completions endpoint and return full response."""
        # Handle both /v1/chat/completions and /chat/completions formats
        if "/v1/" in self._base_url or self._base_url.endswith("/v1"):
            url = f"{self._base_url}/chat/completions"
        else:
            url = f"{self._base_url}/v1/chat/completions"
        if not url.startswith("http"):
            url = f"https://{url}"

        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload: dict[str, Any] = {
            "model": model or self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature if temperature is not None else self._temperature,
        }

        response = self._client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, Mapping):
            raise ValueError("Invalid LLM response: expected object")

        return {
            "content": self._extract_content(data),
            "model": data.get("model", self._model),
            "usage": data.get("usage", {}),
            "raw_response": data,
        }

    def _extract_content(self, data: Mapping[str, Any]) -> str:
        """Extract content from LLM response."""
        choices = data.get("choices")
        if not isinstance(choices, list) or len(choices) == 0:
            raise ValueError("Invalid LLM response: missing choices")
        first = choices[0]
        if not isinstance(first, Mapping):
            raise ValueError("Invalid LLM response: invalid choice")
        message = first.get("message")
        if not isinstance(message, Mapping):
            raise ValueError("Invalid LLM response: missing message")
        content = message.get("content")
        if not isinstance(content, str):
            raise ValueError("Invalid LLM response: missing content")
        return content


_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Get or create LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient(
            base_url=LLM_BASE_URL,
            api_key=LLM_API_KEY,
            model=LLM_MODEL,
            timeout=LLM_TIMEOUT,
            temperature=LLM_TEMPERATURE,
        )
    return _llm_client


def chat_completion_tool(
    system: str,
    user: str,
    temperature: float | None = None,
    model: str | None = None,
) -> dict:
    """Perform a chat completion."""
    start_time = time.time()
    try:
        client = get_llm_client()
        result = client.chat_completion(system=system, user=user, temperature=temperature, model=model)
        elapsed = time.time() - start_time
        return {
            "content": result["content"],
            "model": result["model"],
            "usage": result["usage"],
            "elapsed_seconds": round(elapsed, 3),
        }
    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
        raise ValueError(f"LLM API error: {error_msg}") from e
    except Exception as e:
        raise ValueError(f"LLM error: {str(e)}") from e


@app.post("/mcp")
async def mcp_endpoint(request: MCPRequest):
    """Handle MCP JSON-RPC requests."""
    method = request.method
    params = request.params or {}

    try:
        if method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name == "chat_completion":
                result = chat_completion_tool(
                    system=arguments["system"],
                    user=arguments["user"],
                    temperature=arguments.get("temperature"),
                    model=arguments.get("model"),
                )
            else:
                return MCPResponse(
                    id=request.id,
                    error={"code": -32601, "message": f"Unknown tool: {tool_name}"},
                )

            return MCPResponse(id=request.id, result=result)
        else:
            return MCPResponse(
                id=request.id,
                error={"code": -32601, "message": f"Unknown method: {method}"},
            )
    except KeyError as e:
        return MCPResponse(
            id=request.id,
            error={"code": -32602, "message": f"Missing parameter: {e}"},
        )
    except ValueError as e:
        return MCPResponse(
            id=request.id,
            error={"code": -32603, "message": str(e)},
        )
    except Exception as e:
        return MCPResponse(
            id=request.id,
            error={"code": -32603, "message": f"Internal error: {str(e)}"},
        )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "mcp-llm-server",
        "model": LLM_MODEL,
        "base_url": LLM_BASE_URL,
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("LLM_MCP_SERVER_PORT", "3004"))
    uvicorn.run(app, host="0.0.0.0", port=port)

