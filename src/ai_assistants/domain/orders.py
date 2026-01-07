from __future__ import annotations

from ai_assistants.adapters.registry import get_purchases_adapter
from ai_assistants.domain.purchases.models import Order


def get_order_by_id(order_id: str) -> Order | None:
    """Fetch an order by id from the configured purchases adapter."""
    return get_purchases_adapter().get_order(order_id)


