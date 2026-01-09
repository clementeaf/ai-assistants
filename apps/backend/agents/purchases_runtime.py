from __future__ import annotations

from ai_assistants.agents.purchases_planner import PurchasesPlanner, build_purchases_planner_from_env

_planner: PurchasesPlanner | None = None


def get_purchases_planner() -> PurchasesPlanner | None:
    """Return PurchasesPlanner if enabled and LLM is configured."""
    global _planner
    if _planner is None:
        _planner = build_purchases_planner_from_env()
    return _planner


def set_purchases_planner(planner: PurchasesPlanner | None) -> None:
    """Override planner (tests)."""
    global _planner
    _planner = planner


