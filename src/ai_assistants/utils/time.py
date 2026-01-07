from __future__ import annotations

import os
from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return current UTC time.

    If AI_ASSISTANTS_FIXED_NOW_ISO is set, returns that fixed instant (useful for tests/evals).
    """
    fixed = os.getenv("AI_ASSISTANTS_FIXED_NOW_ISO")
    if fixed is None or fixed.strip() == "":
        return datetime.now(tz=timezone.utc)
    try:
        parsed = datetime.fromisoformat(fixed)
    except ValueError:
        return datetime.now(tz=timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


