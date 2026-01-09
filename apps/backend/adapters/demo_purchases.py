from __future__ import annotations

from datetime import datetime, timezone
from typing import Final

from ai_assistants.adapters.purchases import PurchasesAdapter
from ai_assistants.domain.purchases.models import Order, OrderStatus, Shipment, ShipmentStatus


class DemoPurchasesAdapter(PurchasesAdapter):
    """In-memory demo adapter for purchases and tracking."""

    def __init__(self) -> None:
        self._orders: dict[str, Order] = dict(_DEMO_ORDERS)
        self._shipments_by_order: dict[str, Shipment] = dict(_DEMO_SHIPMENTS_BY_ORDER)
        self._shipments_by_tracking: dict[str, Shipment] = {
            shipment.tracking_id: shipment for shipment in self._shipments_by_order.values()
        }

    def get_order(self, order_id: str) -> Order | None:
        """Return an order by id, or None if not found."""
        return self._orders.get(order_id)

    def list_orders(self, customer_id: str) -> list[Order]:
        """Return orders for the given customer id."""
        return [order for order in self._orders.values() if order.customer_id == customer_id]

    def get_shipment_by_order_id(self, order_id: str) -> Shipment | None:
        """Return shipment for an order, or None if not found."""
        return self._shipments_by_order.get(order_id)

    def get_shipment_by_tracking_id(self, tracking_id: str) -> Shipment | None:
        """Return shipment by tracking id, or None if not found."""
        return self._shipments_by_tracking.get(tracking_id)


_CUSTOMER_A: Final[str] = "+5491112345678"
_CUSTOMER_B: Final[str] = "+5491199999999"

_DEMO_ORDERS: Final[dict[str, Order]] = {
    "ORDER-100": Order(
        order_id="ORDER-100",
        customer_id=_CUSTOMER_A,
        status=OrderStatus.delivered,
        total_amount=39.99,
        currency="USD",
        created_at=datetime(2025, 1, 5, 12, 0, tzinfo=timezone.utc),
    ),
    "ORDER-200": Order(
        order_id="ORDER-200",
        customer_id=_CUSTOMER_A,
        status=OrderStatus.shipped,
        total_amount=120.0,
        currency="USD",
        created_at=datetime(2025, 2, 10, 16, 30, tzinfo=timezone.utc),
    ),
    "ORDER-210": Order(
        order_id="ORDER-210",
        customer_id=_CUSTOMER_A,
        status=OrderStatus.delivered,
        total_amount=15.0,
        currency="USD",
        created_at=datetime(2025, 2, 20, 9, 0, tzinfo=timezone.utc),
    ),
    "ORDER-300": Order(
        order_id="ORDER-300",
        customer_id=_CUSTOMER_B,
        status=OrderStatus.processing,
        total_amount=15.5,
        currency="USD",
        created_at=datetime(2025, 3, 2, 10, 15, tzinfo=timezone.utc),
    ),
}

_DEMO_SHIPMENTS_BY_ORDER: Final[dict[str, Shipment]] = {
    "ORDER-100": Shipment(
        tracking_id="TRACK-9001",
        order_id="ORDER-100",
        carrier="DemoCarrier",
        status=ShipmentStatus.delivered,
        last_update_at=datetime(2025, 1, 8, 12, 0, tzinfo=timezone.utc),
        estimated_delivery_at=datetime(2025, 1, 8, 18, 0, tzinfo=timezone.utc),
    ),
    "ORDER-200": Shipment(
        tracking_id="TRACK-9002",
        order_id="ORDER-200",
        carrier="DemoCarrier",
        status=ShipmentStatus.in_transit,
        last_update_at=datetime(2025, 2, 12, 9, 0, tzinfo=timezone.utc),
        estimated_delivery_at=datetime(2025, 2, 14, 18, 0, tzinfo=timezone.utc),
    ),
    "ORDER-210": Shipment(
        tracking_id="TRACK-9010",
        order_id="ORDER-210",
        carrier="DemoCarrier",
        status=ShipmentStatus.delivered,
        last_update_at=datetime(2025, 2, 22, 12, 0, tzinfo=timezone.utc),
        estimated_delivery_at=datetime(2025, 2, 22, 18, 0, tzinfo=timezone.utc),
    ),
}


