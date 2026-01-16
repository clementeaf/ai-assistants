from __future__ import annotations

from ai_assistants.automata.claims.planner import ClaimsPlanner, build_claims_planner_from_env

_planner: ClaimsPlanner | None = None


def get_claims_planner() -> ClaimsPlanner | None:
    """Return ClaimsPlanner if enabled and LLM is configured."""
    global _planner
    if _planner is None:
        _planner = build_claims_planner_from_env()
    return _planner


def set_claims_planner(planner: ClaimsPlanner | None) -> None:
    """Override planner (tests)."""
    global _planner
    _planner = planner

