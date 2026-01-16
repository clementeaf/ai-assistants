from __future__ import annotations

from ai_assistants.adapters.registry import get_bookings_adapter
from ai_assistants.exceptions.adapter_exceptions import AdapterError, AdapterTimeoutError, AdapterUnavailableError
from ai_assistants.tools.contracts import (
    BookingSlotSummary,
    BookingSummary,
    CheckAvailabilityInput,
    CheckAvailabilityOutput,
    CreateBookingInput,
    CreateBookingOutput,
    DeleteBookingInput,
    DeleteBookingOutput,
    GetAvailableSlotsInput,
    GetAvailableSlotsOutput,
    GetBookingInput,
    GetBookingOutput,
    ListBookingsInput,
    ListBookingsOutput,
    UpdateBookingInput,
    UpdateBookingOutput,
)


def check_availability(input_data: CheckAvailabilityInput) -> CheckAvailabilityOutput:
    """Check if a time slot is available for booking."""
    adapter = get_bookings_adapter()
    try:
        available = adapter.check_availability(
            date_iso=input_data.date_iso,
            start_time_iso=input_data.start_time_iso,
            end_time_iso=input_data.end_time_iso,
            customer_id=input_data.customer_id,
        )
        return CheckAvailabilityOutput(available=available)
    except (AdapterUnavailableError, AdapterTimeoutError) as exc:
        return CheckAvailabilityOutput(available=False, error_code="adapter_error")
    except AdapterError as exc:
        return CheckAvailabilityOutput(available=False, error_code="adapter_error")


def get_available_slots(input_data: GetAvailableSlotsInput) -> GetAvailableSlotsOutput:
    """Get available booking slots for a given date."""
    adapter = get_bookings_adapter()
    try:
        slots = adapter.get_available_slots(date_iso=input_data.date_iso, customer_id=input_data.customer_id)
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
    except (AdapterUnavailableError, AdapterTimeoutError) as exc:
        return GetAvailableSlotsOutput(slots=[], error_code="adapter_error")
    except AdapterError as exc:
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
    except (AdapterUnavailableError, AdapterTimeoutError) as exc:
        return CreateBookingOutput(success=False, error_code="adapter_error")
    except AdapterError as exc:
        return CreateBookingOutput(success=False, error_code="adapter_error")


def get_booking(input_data: GetBookingInput) -> GetBookingOutput:
    """Get a booking by ID."""
    adapter = get_bookings_adapter()
    try:
        booking = adapter.get_booking(booking_id=input_data.booking_id)
        if booking is None:
            return GetBookingOutput(found=False, booking_id=input_data.booking_id)
        return GetBookingOutput(
            found=True,
            booking_id=booking.booking_id,
            customer_id=booking.customer_id,
            customer_name=booking.customer_name,
            date_iso=booking.date_iso,
            start_time_iso=booking.start_time_iso,
            end_time_iso=booking.end_time_iso,
            status=booking.status.value,
            created_at_iso=booking.created_at.isoformat(),
        )
    except (AdapterUnavailableError, AdapterTimeoutError) as exc:
        return GetBookingOutput(found=False, booking_id=input_data.booking_id, error_code="adapter_error")
    except AdapterError as exc:
        return GetBookingOutput(found=False, booking_id=input_data.booking_id, error_code="adapter_error")


def list_bookings(input_data: ListBookingsInput) -> ListBookingsOutput:
    """List bookings for a customer."""
    adapter = get_bookings_adapter()
    try:
        bookings = adapter.list_bookings(customer_id=input_data.customer_id)
        summaries = [
            BookingSummary(
                booking_id=booking.booking_id,
                customer_id=booking.customer_id,
                customer_name=booking.customer_name,
                date_iso=booking.date_iso,
                start_time_iso=booking.start_time_iso,
                end_time_iso=booking.end_time_iso,
                status=booking.status.value,
                created_at_iso=booking.created_at.isoformat(),
            )
            for booking in bookings
        ]
        return ListBookingsOutput(bookings=summaries)
    except (AdapterUnavailableError, AdapterTimeoutError) as exc:
        return ListBookingsOutput(bookings=[], error_code="adapter_error")
    except AdapterError as exc:
        return ListBookingsOutput(bookings=[], error_code="adapter_error")


def update_booking(input_data: UpdateBookingInput) -> UpdateBookingOutput:
    """Update an existing booking."""
    adapter = get_bookings_adapter()
    try:
        booking = adapter.update_booking(
            booking_id=input_data.booking_id,
            date_iso=input_data.date_iso,
            start_time_iso=input_data.start_time_iso,
            end_time_iso=input_data.end_time_iso,
            status=input_data.status,
        )
        if booking is None:
            return UpdateBookingOutput(
                success=False,
                booking_id=input_data.booking_id,
                error_code="booking_not_found",
            )
        return UpdateBookingOutput(
            success=True,
            booking_id=booking.booking_id,
            date_iso=booking.date_iso,
            start_time_iso=booking.start_time_iso,
            end_time_iso=booking.end_time_iso,
            status=booking.status.value,
        )
    except (AdapterUnavailableError, AdapterTimeoutError) as exc:
        return UpdateBookingOutput(
            success=False,
            booking_id=input_data.booking_id,
            error_code="adapter_error",
        )
    except AdapterError as exc:
        return UpdateBookingOutput(
            success=False,
            booking_id=input_data.booking_id,
            error_code="adapter_error",
        )


def delete_booking(input_data: DeleteBookingInput) -> DeleteBookingOutput:
    """Delete a booking."""
    adapter = get_bookings_adapter()
    try:
        success = adapter.delete_booking(booking_id=input_data.booking_id)
        return DeleteBookingOutput(
            success=success,
            booking_id=input_data.booking_id if success else None,
            error_code=None if success else "booking_not_found",
        )
    except (AdapterUnavailableError, AdapterTimeoutError) as exc:
        return DeleteBookingOutput(
            success=False,
            booking_id=input_data.booking_id,
            error_code="adapter_error",
        )
    except AdapterError as exc:
        return DeleteBookingOutput(
            success=False,
            booking_id=input_data.booking_id,
            error_code="adapter_error",
        )

