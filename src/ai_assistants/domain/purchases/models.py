from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class OrderStatus(str, Enum):
    """Supported order statuses."""

    processing = "processing"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"


class ShipmentStatus(str, Enum):
    """Supported shipment/tracking statuses."""

    label_created = "label_created"
    in_transit = "in_transit"
    out_for_delivery = "out_for_delivery"
    delivered = "delivered"
    exception = "exception"


@dataclass(frozen=True, slots=True)
class Order:
    """Purchase order entity."""

    order_id: str
    customer_id: str
    status: OrderStatus
    total_amount: float
    currency: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class Shipment:
    """Shipment entity associated with an order."""

    tracking_id: str
    order_id: str
    carrier: str
    status: ShipmentStatus
    last_update_at: datetime
    estimated_delivery_at: datetime | None


