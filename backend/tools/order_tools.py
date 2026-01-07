from __future__ import annotations

from ai_assistants.tools.contracts import GetOrderInput, GetOrderOutput
from ai_assistants.tools.purchases_tools import get_order as _get_order


def get_order(input_data: GetOrderInput) -> GetOrderOutput:
    """Backward-compatible alias for purchases.get_order."""
    return _get_order(input_data)


