from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel, Field, ValidationError

from ai_assistants.exceptions.adapter_exceptions import AdapterError, AdapterTimeoutError
from ai_assistants.llm.openai_compatible import OpenAICompatibleClient, load_openai_compatible_config
from ai_assistants.observability.logging import get_logger
from ai_assistants.utils.prompts import load_prompt_text


class TextRewriter(Protocol):
    """Protocol for rewriting a draft response into a final message."""

    def rewrite(self, *, user_text: str, draft_text: str, domain: str) -> str:
        """Rewrite the draft response text."""


class NlgRewriteResult(BaseModel):
    """Structured output from the NLG rewriter."""

    text: str = Field(min_length=1)


@dataclass(frozen=True, slots=True)
class NlgConfig:
    """Configuration for NLG rewriting."""

    enabled: bool


def load_nlg_config() -> NlgConfig:
    """Load NLG config from env vars."""
    raw = os.getenv("AI_ASSISTANTS_LLM_NLG_ENABLED", "0").strip().lower()
    enabled = raw in {"1", "true", "yes", "on"}
    return NlgConfig(enabled=enabled)

def _strict_enabled() -> bool:
    raw = os.getenv("AI_ASSISTANTS_LLM_NLG_STRICT", "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


_ORDER_ID_RE = re.compile(r"\bORDER-\d+\b", flags=re.IGNORECASE)
_TRACKING_ID_RE = re.compile(r"\bTRACK-\d+\b", flags=re.IGNORECASE)
_ISO_TS_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})\b")


def _extract_tokens(text: str) -> tuple[set[str], set[str], set[str]]:
    """Extract critical tokens that must be preserved by NLG."""
    order_ids = {m.group(0).upper() for m in _ORDER_ID_RE.finditer(text)}
    tracking_ids = {m.group(0).upper() for m in _TRACKING_ID_RE.finditer(text)}
    timestamps = {m.group(0) for m in _ISO_TS_RE.finditer(text)}
    return order_ids, tracking_ids, timestamps


def _passes_guardrails(*, draft: str, rewritten: str) -> bool:
    """Return true if the rewritten text preserves critical identifiers from draft."""
    draft_orders, draft_tracks, draft_ts = _extract_tokens(draft)
    rw_orders, rw_tracks, rw_ts = _extract_tokens(rewritten)

    # Must preserve all draft IDs/timestamps
    if not draft_orders.issubset(rw_orders):
        return False
    if not draft_tracks.issubset(rw_tracks):
        return False
    if not draft_ts.issubset(rw_ts):
        return False

    # Must NOT introduce new IDs
    if not rw_orders.issubset(draft_orders):
        return False
    if not rw_tracks.issubset(draft_tracks):
        return False

    # Timestamps: allow dropping none, but also disallow adding new ones
    if not rw_ts.issubset(draft_ts):
        return False

    return True


class LlmTextRewriter(TextRewriter):
    """LLM-based rewriter that improves style without adding facts."""

    def __init__(self, client: OpenAICompatibleClient) -> None:
        self._client = client
        self._logger = get_logger()

    def rewrite(self, *, user_text: str, draft_text: str, domain: str) -> str:
        """Rewrite a draft response in Spanish, preserving facts and identifiers."""
        system = load_prompt_text("nlg_rewriter_system.txt")
        user = (
            f"Domain: {domain}\n"
            f"User message: {user_text}\n"
            f"Draft response:\n{draft_text}\n"
        )
        content = self._client.chat_completion(system=system, user=user)
        try:
            parsed = NlgRewriteResult.model_validate(json.loads(content))
            return parsed.text
        except (ValueError, ValidationError) as exc:
            self._logger.warning("nlg.invalid_output", error=str(exc))
            return draft_text


def build_rewriter_from_env() -> TextRewriter | None:
    """Build an LLM rewriter if configured; otherwise return None."""
    cfg = load_nlg_config()
    if not cfg.enabled:
        return None
    llm_cfg = load_openai_compatible_config()
    if llm_cfg is None:
        get_logger().warning("nlg.disabled_missing_llm_config")
        return None
    return LlmTextRewriter(OpenAICompatibleClient(llm_cfg))


def maybe_rewrite(
    *, rewriter: TextRewriter | None, user_text: str, draft_text: str, domain: str
) -> str:
    """Rewrite the draft if a rewriter is provided; otherwise return draft."""
    if rewriter is None:
        return draft_text
    try:
        rewritten = rewriter.rewrite(user_text=user_text, draft_text=draft_text, domain=domain)
        if rewritten.strip() == "":
            return draft_text
        if _strict_enabled() and not _passes_guardrails(draft=draft_text, rewritten=rewritten):
            get_logger().warning("nlg.guardrails.rejected")
            return draft_text
        return rewritten
    except (AdapterError, AdapterTimeoutError, ValidationError, ValueError) as exc:
        get_logger().warning("nlg.error", error=str(exc), error_type=type(exc).__name__)
        return draft_text


