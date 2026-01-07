from __future__ import annotations

from ai_assistants.adapters.bookings import BookingsAdapter
from ai_assistants.adapters.demo_bookings import DemoBookingsAdapter
from ai_assistants.adapters.demo_purchases import DemoPurchasesAdapter
from ai_assistants.adapters.external_hook import ExternalHookPurchasesAdapter, load_external_hook_config
from ai_assistants.adapters.purchases import PurchasesAdapter

_purchases_adapter: PurchasesAdapter | None = None
_bookings_adapter: BookingsAdapter | None = None


def get_purchases_adapter() -> PurchasesAdapter:
    """Return the configured purchases adapter instance.

    For now, this returns an in-memory demo adapter. In production this should be
    backed by real integrations (DB/ERP/OMS).
    """
    global _purchases_adapter
    if _purchases_adapter is None:
        hook_config = load_external_hook_config()
        if hook_config is not None:
            _purchases_adapter = ExternalHookPurchasesAdapter(hook_config)
        else:
            _purchases_adapter = DemoPurchasesAdapter()
    return _purchases_adapter


def set_purchases_adapter(adapter: PurchasesAdapter | None) -> None:
    """Override the purchases adapter instance (used for testing/evals)."""
    global _purchases_adapter
    _purchases_adapter = adapter


def get_bookings_adapter() -> BookingsAdapter:
    """Return the configured bookings adapter instance.

    For now, this returns an in-memory demo adapter. In production this should be
    backed by real integrations (calendar system/booking system).
    """
    global _bookings_adapter
    if _bookings_adapter is None:
        _bookings_adapter = DemoBookingsAdapter()
    return _bookings_adapter


def set_bookings_adapter(adapter: BookingsAdapter | None) -> None:
    """Override the bookings adapter instance (used for testing/evals)."""
    global _bookings_adapter
    _bookings_adapter = adapter


