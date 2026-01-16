from __future__ import annotations

from ai_assistants.agents.autonomous_planner import AutonomousPlanner, build_autonomous_planner_from_env

_planner: AutonomousPlanner | None = None


def get_autonomous_planner() -> AutonomousPlanner | None:
    """Return AutonomousPlanner if enabled and LLM is configured."""
    global _planner
    if _planner is None:
        _planner = build_autonomous_planner_from_env()
    return _planner


def set_autonomous_planner(planner: AutonomousPlanner | None) -> None:
    """Override planner (tests)."""
    global _planner
    _planner = planner
