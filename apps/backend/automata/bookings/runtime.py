from __future__ import annotations

from ai_assistants.automata.bookings.planner import BookingsPlanner, build_bookings_planner_from_env

_planner: BookingsPlanner | None = None


def get_bookings_planner() -> BookingsPlanner | None:
    """Return BookingsPlanner if enabled and LLM is configured."""
    global _planner
    if _planner is None:
        _planner = build_bookings_planner_from_env()
    return _planner


def set_bookings_planner(planner: BookingsPlanner | None) -> None:
    """Override planner (tests)."""
    global _planner
    _planner = planner

