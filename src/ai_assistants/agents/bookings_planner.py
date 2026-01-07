from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal, Protocol

from pydantic import BaseModel, Field, ValidationError

from ai_assistants.llm.openai_compatible import OpenAICompatibleClient, load_openai_compatible_config
from ai_assistants.observability.logging import get_logger
from ai_assistants.utils.prompts import load_prompt_text


class ChatClient(Protocol):
    def chat_completion(self, *, system: str, user: str) -> str:  # pragma: no cover
        ...


ToolName = Literal["get_available_slots", "check_availability", "create_booking", "vector_recall"]


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
class BookingsPlannerConfig:
    enabled: bool


def load_bookings_planner_config() -> BookingsPlannerConfig:
    import os

    raw = os.getenv("AI_ASSISTANTS_BOOKINGS_PLANNER_ENABLED", "0").strip().lower()
    enabled = raw in {"1", "true", "yes", "on"}
    return BookingsPlannerConfig(enabled=enabled)


class BookingsPlanner:
    """LLM-based planner for bookings/reservations domain."""

    def __init__(self, client: ChatClient) -> None:
        self._client = client
        self._logger = get_logger()
        self._system = load_prompt_text("bookings_planner_system.txt")

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
                },
            },
            ensure_ascii=False,
        )
        try:
            content = self._client.chat_completion(system=self._system, user=user)
            parsed = PlannerOutput.model_validate(json.loads(content))
            return parsed
        except (ValueError, ValidationError) as exc:
            self._logger.warning("bookings_planner.invalid_output", error=str(exc))
            return None


def build_bookings_planner_from_env() -> BookingsPlanner | None:
    cfg = load_bookings_planner_config()
    if not cfg.enabled:
        return None
    llm_cfg = load_openai_compatible_config()
    if llm_cfg is None:
        get_logger().warning("bookings_planner.disabled_missing_llm_config")
        return None
    return BookingsPlanner(OpenAICompatibleClient(llm_cfg))

