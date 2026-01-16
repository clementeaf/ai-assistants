"""
API endpoints para gestión completa de autómatas.
Proporciona acceso a versionado, tests, métricas y cambios.
"""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ai_assistants.security.auth import AuthContext, require_auth
from ai_assistants.config.mcp_config import load_mcp_config

router = APIRouter(prefix="/v1/automata", tags=["automata"])


def _get_flow_mcp_url() -> str | None:
    """Obtiene la URL del servidor MCP de flujos."""
    mcp_config = load_mcp_config()
    return mcp_config.booking_flow_server_url


def _call_flow_mcp_tool(tool_name: str, arguments: dict) -> dict:
    """Llama a una herramienta del servidor MCP de flujos."""
    flow_server_url = _get_flow_mcp_url()
    if not flow_server_url:
        raise HTTPException(status_code=503, detail="Flow MCP server not configured")
    
    client = httpx.Client(timeout=10.0)
    try:
        response = client.post(
            f"{flow_server_url}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments},
            },
        )
        response.raise_for_status()
        json_response = response.json()
        if json_response.get("error"):
            error_msg = json_response["error"].get("message", "Unknown MCP error")
            raise HTTPException(status_code=500, detail=f"MCP Error: {error_msg}")
        return json_response.get("result", {})
    except httpx.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"Failed to connect to Flow MCP server: {str(e)}")
    finally:
        client.close()


class CreateAutomatonVersionRequest(BaseModel):
    """Request para crear una nueva versión del prompt del autómata."""

    system_prompt: str
    change_description: str
    created_by: str | None = None


class CreateAutomatonTestRequest(BaseModel):
    """Request para crear un test del autómata."""

    test_name: str
    test_description: str | None = None
    test_type: str
    test_scenario: dict
    expected_result: dict | None = None
    created_by: str | None = None


# Rutas de dominios (deben ir ANTES de la ruta genérica /{automaton_id})
@router.get("/domains/list")
def list_domains(
    auth: AuthContext = Depends(require_auth),
) -> dict:
    """Obtiene lista de dominios disponibles con su metadata para el frontend."""
    _bind_auth_context(auth)
    _enforce_rate_limit(auth)
    from ai_assistants.automata.registry import get_domains_list
    domains = get_domains_list()
    return {"domains": domains, "count": len(domains)}


@router.get("/domains/{domain}/tools")
def get_domain_tools(
    domain: str,
    auth: AuthContext = Depends(require_auth),
) -> dict:
    """Obtiene las herramientas disponibles para un dominio específico."""
    _bind_auth_context(auth)
    _enforce_rate_limit(auth)
    from ai_assistants.automata.registry import get_automaton_tools
    tools = get_automaton_tools(domain)
    return {"domain": domain, "tools": tools, "count": len(tools)}


@router.get("/domains/{domain}/metadata")
def get_domain_metadata(
    domain: str,
    auth: AuthContext = Depends(require_auth),
) -> dict:
    """Obtiene metadata completa de un dominio (nombre, descripción, código de activación, etc.)."""
    _bind_auth_context(auth)
    _enforce_rate_limit(auth)
    from ai_assistants.automata.registry import get_automaton_metadata
    metadata = get_automaton_metadata(domain)
    if metadata is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Domain '{domain}' not found")
    return {
        "domain": metadata.domain,
        "display_name": metadata.display_name,
        "description": metadata.description,
        "activation_code": metadata.activation_code,
        "tools": metadata.tools,
        "is_enabled": metadata.is_enabled,
    }


@router.get("/{automaton_id}")
def get_automaton(
    automaton_id: str,
    auth: AuthContext = Depends(require_auth),
) -> dict:
    """Obtiene información completa de un autómata."""
    _bind_auth_context(auth)
    _enforce_rate_limit(auth)
    result = _call_flow_mcp_tool("get_automaton", {"automaton_id": automaton_id})
    return result


@router.get("")
def list_automata(
    domain: str | None = None,
    include_inactive: bool = False,
    auth: AuthContext = Depends(require_auth),
) -> dict:
    """Lista todos los autómatas."""
    _bind_auth_context(auth)
    _enforce_rate_limit(auth)
    result = _call_flow_mcp_tool("list_automata", {
        "domain": domain,
        "include_inactive": include_inactive,
    })
    return result


@router.post("/{automaton_id}/versions")
def create_automaton_version(
    automaton_id: str,
    payload: CreateAutomatonVersionRequest,
    auth: AuthContext = Depends(require_auth),
) -> dict:
    """Crea una nueva versión del prompt del autómata."""
    _bind_auth_context(auth)
    _enforce_rate_limit(auth)
    result = _call_flow_mcp_tool("create_automaton_version", {
        "automaton_id": automaton_id,
        "system_prompt": payload.system_prompt,
        "change_description": payload.change_description,
        "created_by": payload.created_by,
    })
    return result


@router.post("/{automaton_id}/tests")
def create_automaton_test(
    automaton_id: str,
    payload: CreateAutomatonTestRequest,
    auth: AuthContext = Depends(require_auth),
) -> dict:
    """Crea un test para el autómata."""
    _bind_auth_context(auth)
    _enforce_rate_limit(auth)
    result = _call_flow_mcp_tool("create_automaton_test", {
        "automaton_id": automaton_id,
        "test_name": payload.test_name,
        "test_description": payload.test_description,
        "test_type": payload.test_type,
        "test_scenario": payload.test_scenario,
        "expected_result": payload.expected_result,
        "created_by": payload.created_by,
    })
    return result


@router.get("/{automaton_id}/test-results")
def get_automaton_test_results(
    automaton_id: str,
    test_id: str | None = None,
    limit: int = 50,
    auth: AuthContext = Depends(require_auth),
) -> dict:
    """Obtiene resultados de tests de un autómata."""
    _bind_auth_context(auth)
    _enforce_rate_limit(auth)
    result = _call_flow_mcp_tool("get_automaton_test_results", {
        "automaton_id": automaton_id,
        "test_id": test_id,
        "limit": limit,
    })
    return result


@router.get("/{automaton_id}/metrics")
def get_automaton_metrics(
    automaton_id: str,
    metric_type: str | None = None,
    limit: int = 50,
    auth: AuthContext = Depends(require_auth),
) -> dict:
    """Obtiene métricas de un autómata."""
    _bind_auth_context(auth)
    _enforce_rate_limit(auth)
    result = _call_flow_mcp_tool("get_automaton_metrics", {
        "automaton_id": automaton_id,
        "metric_type": metric_type,
        "limit": limit,
    })
    return result


@router.get("/{automaton_id}/changes")
def get_automaton_changes(
    automaton_id: str,
    limit: int = 50,
    auth: AuthContext = Depends(require_auth),
) -> dict:
    """Obtiene el historial de cambios de un autómata."""
    _bind_auth_context(auth)
    _enforce_rate_limit(auth)
    result = _call_flow_mcp_tool("get_automaton_changes", {
        "automaton_id": automaton_id,
        "limit": limit,
    })
    return result


# Funciones que serán inyectadas desde app.py
_bind_auth_context_func = None
_enforce_rate_limit_func = None


def set_auth_functions(bind_func, rate_limit_func) -> None:
    """Establece las funciones de autenticación y rate limiting desde app.py."""
    global _bind_auth_context_func, _enforce_rate_limit_func
    _bind_auth_context_func = bind_func
    _enforce_rate_limit_func = rate_limit_func


def _bind_auth_context(auth: AuthContext) -> None:
    """Bind auth context."""
    if _bind_auth_context_func:
        _bind_auth_context_func(auth)


def _enforce_rate_limit(auth: AuthContext) -> None:
    """Enforce rate limit."""
    if _enforce_rate_limit_func:
        _enforce_rate_limit_func(auth)
