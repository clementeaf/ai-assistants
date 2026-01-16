from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Literal, Protocol

from pydantic import BaseModel, Field, ValidationError

from ai_assistants.llm.openai_compatible import OpenAICompatibleClient, load_openai_compatible_config
from ai_assistants.observability.logging import get_logger
from pathlib import Path


class ChatClient(Protocol):
    def chat_completion(self, *, system: str, user: str) -> str:  # pragma: no cover
        ...


ToolName = Literal["get_order", "vector_recall"]


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
class ClaimsPlannerConfig:
    enabled: bool


def load_claims_planner_config() -> ClaimsPlannerConfig:
    import os

    raw = os.getenv("AI_ASSISTANTS_CLAIMS_PLANNER_ENABLED", "0").strip().lower()
    enabled = raw in {"1", "true", "yes", "on"}
    return ClaimsPlannerConfig(enabled=enabled)


_ORDER_ID_RE = re.compile(r"\bORDER-\d+\b", flags=re.IGNORECASE)


class ClaimsPlanner:
    """LLM-based planner for claims/complaints domain."""

    def __init__(self, client: ChatClient) -> None:
        self._client = client
        self._logger = get_logger()
        # Cargar prompt desde la carpeta del autómata
        prompt_path = Path(__file__).parent / "prompt.txt"
        with open(prompt_path, "r", encoding="utf-8") as f:
            self._system = f.read()

    def plan(
        self,
        *,
        user_text: str,
        customer_id: str | None,
    ) -> PlannerOutput | None:
        user = json.dumps(
            {
                "user_text": user_text,
                "context": {
                    "customer_id": customer_id,
                    "explicit_order_ids": list({m.group(0).upper() for m in _ORDER_ID_RE.finditer(user_text)}),
                },
            },
            ensure_ascii=False,
        )
        try:
            content = self._client.chat_completion(system=self._system, user=user)
            parsed = PlannerOutput.model_validate(json.loads(content))
            return parsed
        except (ValueError, ValidationError) as exc:
            self._logger.warning("claims_planner.invalid_output", error=str(exc))
            return None


def build_claims_planner_from_env() -> ClaimsPlanner | None:
    cfg = load_claims_planner_config()
    if not cfg.enabled:
        return None
    llm_cfg = load_openai_compatible_config()
    if llm_cfg is None:
        get_logger().warning("claims_planner.disabled_missing_llm_config")
        return None
    return ClaimsPlanner(OpenAICompatibleClient(llm_cfg))

