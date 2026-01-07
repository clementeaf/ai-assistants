from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Literal, Protocol

from pydantic import BaseModel, Field, ValidationError

from ai_assistants.llm.openai_compatible import OpenAICompatibleClient, load_openai_compatible_config
from ai_assistants.observability.logging import get_logger
from ai_assistants.utils.prompts import load_prompt_text


class ChatClient(Protocol):
    def chat_completion(self, *, system: str, user: str) -> str:  # pragma: no cover
        ...


ToolName = Literal["get_order", "get_tracking_status", "list_orders", "vector_recall"]


class ToolCallAction(BaseModel):
    type: Literal["tool_call"]
    tool: ToolName
    args: dict[str, object] = Field(default_factory=dict)


class AskUserAction(BaseModel):
    type: Literal["ask_user"]
    text: str = Field(min_length=1)


PlannerAction = ToolCallAction | AskUserAction


class PlannerOutput(BaseModel):
    kind: Literal["plan"]
    actions: list[PlannerAction] = Field(default_factory=list, max_length=2)


@dataclass(frozen=True, slots=True)
class PurchasesPlannerConfig:
    enabled: bool


def load_purchases_planner_config() -> PurchasesPlannerConfig:
    import os

    raw = os.getenv("AI_ASSISTANTS_PURCHASES_PLANNER_ENABLED", "0").strip().lower()
    enabled = raw in {"1", "true", "yes", "on"}
    return PurchasesPlannerConfig(enabled=enabled)


_ORDER_ID_RE = re.compile(r"\bORDER-\d+\b", flags=re.IGNORECASE)
_TRACKING_ID_RE = re.compile(r"\bTRACK-\d+\b", flags=re.IGNORECASE)


class PurchasesPlanner:
    """LLM-based planner that returns strict, validated tool calls (no execution)."""

    def __init__(self, client: ChatClient) -> None:
        self._client = client
        self._logger = get_logger()
        self._system = load_prompt_text("purchases_planner_system.txt")

    def plan(
        self,
        *,
        user_text: str,
        customer_id: str | None,
        last_order_id: str | None,
        last_tracking_id: str | None,
    ) -> PlannerOutput | None:
        user = json.dumps(
            {
                "user_text": user_text,
                "context": {
                    "customer_id": customer_id,
                    "last_order_id": last_order_id,
                    "last_tracking_id": last_tracking_id,
                    "explicit_order_ids": list({m.group(0).upper() for m in _ORDER_ID_RE.finditer(user_text)}),
                    "explicit_tracking_ids": list({m.group(0).upper() for m in _TRACKING_ID_RE.finditer(user_text)}),
                },
            },
            ensure_ascii=False,
        )
        try:
            content = self._client.chat_completion(system=self._system, user=user)
            parsed = PlannerOutput.model_validate(json.loads(content))
            return parsed
        except (ValueError, ValidationError) as exc:
            self._logger.warning("purchases_planner.invalid_output", error=str(exc))
            return None


def build_purchases_planner_from_env() -> PurchasesPlanner | None:
    cfg = load_purchases_planner_config()
    if not cfg.enabled:
        return None
    llm_cfg = load_openai_compatible_config()
    if llm_cfg is None:
        get_logger().warning("purchases_planner.disabled_missing_llm_config")
        return None
    return PurchasesPlanner(OpenAICompatibleClient(llm_cfg))


