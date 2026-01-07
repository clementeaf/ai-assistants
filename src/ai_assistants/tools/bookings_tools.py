from __future__ import annotations

from ai_assistants.adapters.registry import get_bookings_adapter
from ai_assistants.tools.contracts import (
    BookingSlotSummary,
    CheckAvailabilityInput,
    CheckAvailabilityOutput,
    CreateBookingInput,
    CreateBookingOutput,
    GetAvailableSlotsInput,
    GetAvailableSlotsOutput,
)


def check_availability(input_data: CheckAvailabilityInput) -> CheckAvailabilityOutput:
    """Check if a time slot is available for booking."""
    adapter = get_bookings_adapter()
    try:
        available = adapter.check_availability(
            date_iso=input_data.date_iso,
            start_time_iso=input_data.start_time_iso,
            end_time_iso=input_data.end_time_iso,
        )
        return CheckAvailabilityOutput(available=available)
    except Exception:  # noqa: BLE001
        return CheckAvailabilityOutput(available=False, error_code="adapter_error")


def get_available_slots(input_data: GetAvailableSlotsInput) -> GetAvailableSlotsOutput:
    """Get available booking slots for a given date."""
    adapter = get_bookings_adapter()
    try:
        slots = adapter.get_available_slots(date_iso=input_data.date_iso)
        summaries = [
            BookingSlotSummary(
                date_iso=slot.date_iso,
                start_time_iso=slot.start_time_iso,
                end_time_iso=slot.end_time_iso,
                available=slot.available,
            )
            for slot in slots
        ]
        return GetAvailableSlotsOutput(slots=summaries)
    except Exception:  # noqa: BLE001
        return GetAvailableSlotsOutput(slots=[], error_code="adapter_error")


def create_booking(input_data: CreateBookingInput) -> CreateBookingOutput:
    """Create a new booking."""
    adapter = get_bookings_adapter()
    try:
        booking = adapter.create_booking(
            customer_id=input_data.customer_id,
            customer_name=input_data.customer_name,
            date_iso=input_data.date_iso,
            start_time_iso=input_data.start_time_iso,
            end_time_iso=input_data.end_time_iso,
        )
        return CreateBookingOutput(
            success=True,
            booking_id=booking.booking_id,
            date_iso=booking.date_iso,
            start_time_iso=booking.start_time_iso,
            end_time_iso=booking.end_time_iso,
        )
    except Exception:  # noqa: BLE001
        return CreateBookingOutput(success=False, error_code="adapter_error")

