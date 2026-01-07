from __future__ import annotations

from typing import Protocol

from ai_assistants.domain.purchases.models import Order, Shipment


class PurchasesAdapter(Protocol):
    """Adapter interface for purchases and tracking operations."""

    def get_order(self, order_id: str) -> Order | None:
        """Return an order by id, or None if not found."""

    def list_orders(self, customer_id: str) -> list[Order]:
        """Return orders for the given customer id."""

    def get_shipment_by_order_id(self, order_id: str) -> Shipment | None:
        """Return shipment for an order, or None if not found."""

    def get_shipment_by_tracking_id(self, tracking_id: str) -> Shipment | None:
        """Return shipment by tracking id, or None if not found."""


