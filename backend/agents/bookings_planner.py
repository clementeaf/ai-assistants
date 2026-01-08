from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal, Protocol

from pydantic import BaseModel, Field, ValidationError

from ai_assistants.adapters.mcp_llm_adapter import MCPLLMAdapter
from ai_assistants.adapters.mcp_llm_config import load_mcp_llm_config
from ai_assistants.llm.chat_client import ChatClient
from ai_assistants.llm.openai_compatible import OpenAICompatibleClient, load_openai_compatible_config
from ai_assistants.observability.logging import get_logger
from ai_assistants.utils.prompts import load_prompt_text


ToolName = Literal[
    "get_available_slots",
    "check_availability",
    "create_booking",
    "get_booking",
    "list_bookings",
    "update_booking",
    "delete_booking",
    "vector_recall",
]


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
        customer_name: str | None = None,
        requested_booking_date: str | None = None,
        requested_booking_start_time: str | None = None,
        requested_booking_end_time: str | None = None,
    ) -> PlannerOutput | None:
        user = json.dumps(
            {
                "user_text": user_text,
                "context": {
                    "customer_id": customer_id,
                    "customer_name": customer_name,
                    "requested_booking_date": requested_booking_date,
                    "requested_booking_start_time": requested_booking_start_time,
                    "requested_booking_end_time": requested_booking_end_time,
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

    # Priority: MCP LLM adapter > Direct OpenAI-compatible client
    mcp_llm_cfg = load_mcp_llm_config()
    if mcp_llm_cfg is not None:
        return BookingsPlanner(MCPLLMAdapter(mcp_llm_cfg.server_url, mcp_llm_cfg.api_key, mcp_llm_cfg.timeout_seconds))

    llm_cfg = load_openai_compatible_config()
    if llm_cfg is None:
        get_logger().warning("bookings_planner.disabled_missing_llm_config")
        return None
    return BookingsPlanner(OpenAICompatibleClient(llm_cfg))

