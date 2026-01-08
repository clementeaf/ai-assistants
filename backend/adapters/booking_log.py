from __future__ import annotations

from typing import Protocol

from ai_assistants.domain.booking_log.models import BookingLog


class BookingLogAdapter(Protocol):
    """Adapter interface for booking log operations."""

    def create_booking_log(
        self,
        booking_code: str,
        customer_name: str,
        customer_id: str | None = None,
        date_iso: str | None = None,
        time_iso: str | None = None,
        area_id: str | None = None,
        area_name: str | None = None,
        specialty_id: str | None = None,
        specialty_name: str | None = None,
        professional_id: str | None = None,
        professional_name: str | None = None,
        observations: str | None = None,
    ) -> BookingLog:
        """Create a new booking log entry."""

    def get_booking_log(self, booking_code: str | None = None, log_id: str | None = None) -> BookingLog | None:
        """Get a booking log by booking code or log ID."""

    def list_booking_logs(
        self,
        customer_id: str | None = None,
        customer_name: str | None = None,
        date_iso: str | None = None,
        professional_id: str | None = None,
        specialty_id: str | None = None,
        area_id: str | None = None,
        limit: int = 100,
    ) -> list[BookingLog]:
        """List booking logs with optional filters."""

    def update_booking_log(
        self,
        booking_code: str | None = None,
        log_id: str | None = None,
        customer_name: str | None = None,
        date_iso: str | None = None,
        time_iso: str | None = None,
        area_id: str | None = None,
        area_name: str | None = None,
        specialty_id: str | None = None,
        specialty_name: str | None = None,
        professional_id: str | None = None,
        professional_name: str | None = None,
        observations: str | None = None,
    ) -> BookingLog | None:
        """Update a booking log entry."""

    def delete_booking_log(self, booking_code: str | None = None, log_id: str | None = None) -> bool:
        """Delete a booking log entry."""

