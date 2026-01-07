from __future__ import annotations

from typing import Protocol

from ai_assistants.domain.bookings.models import Booking, BookingSlot


class BookingsAdapter(Protocol):
    """Adapter interface for bookings and reservations operations."""

    def check_availability(self, date_iso: str, start_time_iso: str, end_time_iso: str) -> bool:
        """Check if a time slot is available for booking."""

    def get_available_slots(self, date_iso: str) -> list[BookingSlot]:
        """Return available booking slots for a given date."""

    def create_booking(
        self,
        customer_id: str,
        customer_name: str,
        date_iso: str,
        start_time_iso: str,
        end_time_iso: str,
    ) -> Booking:
        """Create a new booking and return it."""

    def get_booking(self, booking_id: str) -> Booking | None:
        """Return a booking by id, or None if not found."""

    def list_bookings(self, customer_id: str) -> list[Booking]:
        """Return bookings for the given customer id."""

