from __future__ import annotations

from ai_assistants.adapters.registry import get_purchases_adapter
from ai_assistants.adapters.external_hook import ExternalHookPurchasesAdapter
from ai_assistants.tools.contracts import (
    GetOrderInput,
    GetOrderOutput,
    GetTrackingInput,
    GetTrackingOutput,
    ListOrdersInput,
    ListOrdersOutput,
    OrderSummary,
)


def get_order(input_data: GetOrderInput) -> GetOrderOutput:
    """Fetch an order with validated input and a stable output schema."""
    adapter = get_purchases_adapter()
    try:
        order = adapter.get_order(input_data.order_id)
    except ExternalHookPurchasesAdapter.HookUnavailableError:
        return GetOrderOutput(
            found=False,
            order_id=None,
            customer_id=None,
            status=None,
            total_amount=None,
            currency=None,
            created_at_iso=None,
            tracking_id=None,
            error_code="hook_unavailable",
        )
    if order is None:
        return GetOrderOutput(
            found=False,
            order_id=None,
            customer_id=None,
            status=None,
            total_amount=None,
            currency=None,
            created_at_iso=None,
            tracking_id=None,
        )

    try:
        shipment = adapter.get_shipment_by_order_id(order.order_id)
    except ExternalHookPurchasesAdapter.HookUnavailableError:
        shipment = None
    tracking_id = shipment.tracking_id if shipment is not None else None

    return GetOrderOutput(
        found=True,
        order_id=order.order_id,
        customer_id=order.customer_id,
        status=order.status.value,
        total_amount=order.total_amount,
        currency=order.currency,
        created_at_iso=order.created_at.isoformat(),
        tracking_id=tracking_id,
    )


def list_orders(input_data: ListOrdersInput) -> ListOrdersOutput:
    """List orders for a customer id."""
    adapter = get_purchases_adapter()
    try:
        orders = adapter.list_orders(input_data.customer_id)
    except ExternalHookPurchasesAdapter.HookUnavailableError:
        return ListOrdersOutput(orders=[], error_code="hook_unavailable")
    orders_sorted = sorted(orders, key=lambda o: o.created_at, reverse=True)

    summaries: list[OrderSummary] = []
    for order in orders_sorted:
        shipment = adapter.get_shipment_by_order_id(order.order_id)
        summaries.append(
            OrderSummary(
                order_id=order.order_id,
                status=order.status.value,
                total_amount=order.total_amount,
                currency=order.currency,
                created_at_iso=order.created_at.isoformat(),
                tracking_id=shipment.tracking_id if shipment is not None else None,
            )
        )
    return ListOrdersOutput(orders=summaries)


def get_tracking_status(input_data: GetTrackingInput) -> GetTrackingOutput:
    """Fetch tracking status either by order_id or by tracking_id."""
    adapter = get_purchases_adapter()

    shipment = None
    try:
        if input_data.tracking_id is not None:
            shipment = adapter.get_shipment_by_tracking_id(input_data.tracking_id)
        elif input_data.order_id is not None:
            shipment = adapter.get_shipment_by_order_id(input_data.order_id)
    except ExternalHookPurchasesAdapter.HookUnavailableError:
        return GetTrackingOutput(
            found=False,
            tracking_id=None,
            order_id=None,
            carrier=None,
            status=None,
            last_update_iso=None,
            estimated_delivery_iso=None,
            error_code="hook_unavailable",
        )

    if shipment is None:
        return GetTrackingOutput(
            found=False,
            tracking_id=None,
            order_id=None,
            carrier=None,
            status=None,
            last_update_iso=None,
            estimated_delivery_iso=None,
        )

    return GetTrackingOutput(
        found=True,
        tracking_id=shipment.tracking_id,
        order_id=shipment.order_id,
        carrier=shipment.carrier,
        status=shipment.status.value,
        last_update_iso=shipment.last_update_at.isoformat(),
        estimated_delivery_iso=shipment.estimated_delivery_at.isoformat() if shipment.estimated_delivery_at else None,
    )


