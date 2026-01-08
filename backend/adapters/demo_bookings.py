from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Final

from ai_assistants.adapters.bookings import BookingsAdapter
from ai_assistants.domain.bookings.models import Booking, BookingSlot, BookingStatus


class DemoBookingsAdapter(BookingsAdapter):
    """In-memory demo adapter for bookings and reservations."""

    def __init__(self) -> None:
        self._bookings: dict[str, Booking] = {}
        self._available_slots: dict[str, list[BookingSlot]] = {
            "2025-03-15": [
                BookingSlot(
                    date_iso="2025-03-15",
                    start_time_iso="2025-03-15T09:00:00Z",
                    end_time_iso="2025-03-15T10:00:00Z",
                    available=True,
                ),
                BookingSlot(
                    date_iso="2025-03-15",
                    start_time_iso="2025-03-15T10:00:00Z",
                    end_time_iso="2025-03-15T11:00:00Z",
                    available=True,
                ),
                BookingSlot(
                    date_iso="2025-03-15",
                    start_time_iso="2025-03-15T14:00:00Z",
                    end_time_iso="2025-03-15T15:00:00Z",
                    available=True,
                ),
                BookingSlot(
                    date_iso="2025-03-15",
                    start_time_iso="2025-03-15T15:00:00Z",
                    end_time_iso="2025-03-15T16:00:00Z",
                    available=False,
                ),
            ],
            "2025-03-16": [
                BookingSlot(
                    date_iso="2025-03-16",
                    start_time_iso="2025-03-16T09:00:00Z",
                    end_time_iso="2025-03-16T10:00:00Z",
                    available=True,
                ),
                BookingSlot(
                    date_iso="2025-03-16",
                    start_time_iso="2025-03-16T10:00:00Z",
                    end_time_iso="2025-03-16T11:00:00Z",
                    available=True,
                ),
                BookingSlot(
                    date_iso="2025-03-16",
                    start_time_iso="2025-03-16T14:00:00Z",
                    end_time_iso="2025-03-16T15:00:00Z",
                    available=True,
                ),
            ],
        }

    def check_availability(self, date_iso: str, start_time_iso: str, end_time_iso: str) -> bool:
        """Check if a time slot is available for booking."""
        slots = self._available_slots.get(date_iso, [])
        for slot in slots:
            if slot.start_time_iso == start_time_iso and slot.end_time_iso == end_time_iso:
                if not slot.available:
                    return False
                for booking in self._bookings.values():
                    if (
                        booking.date_iso == date_iso
                        and booking.start_time_iso == start_time_iso
                        and booking.end_time_iso == end_time_iso
                        and booking.status in (BookingStatus.pending, BookingStatus.confirmed)
                    ):
                        return False
                return True
        return False

    def get_available_slots(self, date_iso: str) -> list[BookingSlot]:
        """Return available booking slots for a given date."""
        slots = self._available_slots.get(date_iso, [])
        available = []
        for slot in slots:
            if not slot.available:
                continue
            is_booked = any(
                booking.date_iso == date_iso
                and booking.start_time_iso == slot.start_time_iso
                and booking.end_time_iso == slot.end_time_iso
                and booking.status in (BookingStatus.pending, BookingStatus.confirmed)
                for booking in self._bookings.values()
            )
            if not is_booked:
                available.append(slot)
        return available

    def create_booking(
        self,
        customer_id: str,
        customer_name: str,
        date_iso: str,
        start_time_iso: str,
        end_time_iso: str,
    ) -> Booking:
        """Create a new booking and return it."""
        booking_id = f"BOOKING-{uuid.uuid4().hex[:8].upper()}"
        booking = Booking(
            booking_id=booking_id,
            customer_id=customer_id,
            customer_name=customer_name,
            date_iso=date_iso,
            start_time_iso=start_time_iso,
            end_time_iso=end_time_iso,
            status=BookingStatus.confirmed,
            created_at=datetime.now(tz=timezone.utc),
            confirmation_email_sent=False,
            reminder_sent=False,
        )
        self._bookings[booking_id] = booking
        return booking

    def get_booking(self, booking_id: str) -> Booking | None:
        """Return a booking by id, or None if not found."""
        return self._bookings.get(booking_id)

    def list_bookings(self, customer_id: str) -> list[Booking]:
        """Return bookings for the given customer id."""
        return [booking for booking in self._bookings.values() if booking.customer_id == customer_id]

    def update_booking(
        self,
        booking_id: str,
        date_iso: str | None = None,
        start_time_iso: str | None = None,
        end_time_iso: str | None = None,
        status: str | None = None,
    ) -> Booking | None:
        """Update an existing booking. Returns the updated booking or None if not found."""
        booking = self._bookings.get(booking_id)
        if booking is None:
            return None

        updated_fields = {}
        if date_iso is not None:
            updated_fields["date_iso"] = date_iso
        if start_time_iso is not None:
            updated_fields["start_time_iso"] = start_time_iso
        if end_time_iso is not None:
            updated_fields["end_time_iso"] = end_time_iso
        if status is not None:
            try:
                updated_fields["status"] = BookingStatus(status)
            except ValueError:
                return None

        updated_booking = Booking(
            booking_id=booking.booking_id,
            customer_id=booking.customer_id,
            customer_name=booking.customer_name,
            date_iso=updated_fields.get("date_iso", booking.date_iso),
            start_time_iso=updated_fields.get("start_time_iso", booking.start_time_iso),
            end_time_iso=updated_fields.get("end_time_iso", booking.end_time_iso),
            status=updated_fields.get("status", booking.status),
            created_at=booking.created_at,
            confirmation_email_sent=booking.confirmation_email_sent,
            reminder_sent=booking.reminder_sent,
        )
        self._bookings[booking_id] = updated_booking
        return updated_booking

    def delete_booking(self, booking_id: str) -> bool:
        """Delete a booking. Returns True if deleted, False if not found."""
        if booking_id not in self._bookings:
            return False
        del self._bookings[booking_id]
        return True

