from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

from ai_assistants.config.llm_config import load_llm_config
from ai_assistants.llm.openai_compatible import OpenAICompatibleClient
from ai_assistants.observability.logging import get_logger
from ai_assistants.utils.prompts import load_prompt_text

Domain = Literal["bookings", "purchases", "claims", "autonomous", "unknown"]


class RouterDecision(BaseModel):
    """Structured router output produced by the LLM router."""

    domain: Domain
    confidence: float = Field(ge=0.0, le=1.0)


@dataclass(frozen=True, slots=True)
class RouterConfig:
    """Router configuration toggles."""

    enabled: bool


def load_router_config() -> RouterConfig:
    """Load router config from env vars."""
    llm_cfg = load_llm_config()
    return RouterConfig(enabled=llm_cfg.router_enabled)


def route_domain_rules(user_text: str) -> Domain:
    """Rule-based router (no external dependencies)."""
    text = user_text.lower().strip()
    
    # Detectar "menu" o "menú" antes de cualquier otra cosa
    if text == "menu" or text == "menú":
        return "unknown"  # Ir a unknown_node para mostrar el menú
    
    if any(word in text for word in ("reclamo", "reclamos", "devolución", "devolucion", "queja")):
        return "claims"
    if any(
        word in text
        for word in (
            "compra",
            "compras",
            "compré",
            "compre",
            "orden",
            "pedido",
            "pedí",
            "pedi",
            "order-",
            "seguimiento",
            "envío",
            "envio",
            "tracking",
            "track-",
        )
    ):
        return "purchases"
    if any(word in text for word in ("reserva", "reservas", "turno", "agenda")):
        return "bookings"
    # Si no detecta palabras clave específicas, usar bookings por defecto
    # (permite que los flujos de bookings funcionen con saludos simples como "Hola")
    return "bookings"


def route_domain(user_text: str) -> Domain:
    """Route the request to a domain using optional LLM router with safe fallback."""
    logger = get_logger()
    cfg = load_router_config()
    if not cfg.enabled:
        return route_domain_rules(user_text)

    llm_cfg = load_llm_config()
    if llm_cfg.base_url is None or llm_cfg.api_key is None or llm_cfg.model is None:
        logger.warning("router.llm.disabled_missing_config")
        return route_domain_rules(user_text)

    from ai_assistants.llm.openai_compatible import OpenAICompatibleConfig, OpenAICompatibleClient
    
    openai_cfg = OpenAICompatibleConfig(
        base_url=llm_cfg.base_url,
        api_key=llm_cfg.api_key,
        model=llm_cfg.model,
        timeout_seconds=llm_cfg.timeout_seconds,
    )

    system = load_prompt_text("router_system.txt")
    user = f"User message:\n{user_text}"

    client = OpenAICompatibleClient(openai_cfg)
    try:
        content = client.chat_completion(system=system, user=user)
        decision = RouterDecision.model_validate(json.loads(content))
        return decision.domain
    except (ValueError, ValidationError) as exc:
        logger.warning("router.llm.invalid_output", error=str(exc))
        return route_domain_rules(user_text)


