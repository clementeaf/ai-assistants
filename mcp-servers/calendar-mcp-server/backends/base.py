"""Base interface for calendar backends."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class CalendarBackend(ABC):
    """Base interface for calendar storage backends."""

    @abstractmethod
    def check_availability(self, date_iso: str, start_time_iso: str, end_time_iso: str) -> bool:
        """
        Check if a time slot is available for booking.
        @param date_iso - Date in ISO format (YYYY-MM-DD)
        @param start_time_iso - Start time in ISO format
        @param end_time_iso - End time in ISO format
        @returns True if available, False otherwise
        """
        pass

    @abstractmethod
    def get_available_slots(self, date_iso: str) -> list[dict[str, Any]]:
        """
        Get available slots for a given date.
        @param date_iso - Date in ISO format (YYYY-MM-DD)
        @returns List of available slots with date_iso, start_time_iso, end_time_iso, available
        """
        pass

    @abstractmethod
    def create_booking(
        self,
        customer_id: str,
        customer_name: str,
        date_iso: str,
        start_time_iso: str,
        end_time_iso: str,
    ) -> dict[str, Any]:
        """
        Create a new booking.
        @param customer_id - Customer identifier
        @param customer_name - Customer name
        @param date_iso - Date in ISO format (YYYY-MM-DD)
        @param start_time_iso - Start time in ISO format
        @param end_time_iso - End time in ISO format
        @returns Booking dictionary with booking_id, customer_id, customer_name, etc.
        """
        pass

    @abstractmethod
    def get_booking(self, booking_id: str) -> dict[str, Any] | None:
        """
        Get a booking by ID.
        @param booking_id - Booking identifier
        @returns Booking dictionary or None if not found
        """
        pass

    @abstractmethod
    def list_bookings(self, customer_id: str) -> list[dict[str, Any]]:
        """
        List bookings for a customer.
        @param customer_id - Customer identifier
        @returns List of booking dictionaries
        """
        pass

    @abstractmethod
    def update_booking(
        self,
        booking_id: str,
        date_iso: str | None = None,
        start_time_iso: str | None = None,
        end_time_iso: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Update an existing booking.
        @param booking_id - Booking identifier
        @param date_iso - New date (optional)
        @param start_time_iso - New start time (optional)
        @param end_time_iso - New end time (optional)
        @param status - New status (optional)
        @returns Updated booking dictionary or None if not found
        """
        pass

    @abstractmethod
    def delete_booking(self, booking_id: str) -> bool:
        """
        Delete a booking.
        @param booking_id - Booking identifier
        @returns True if deleted, False if not found
        """
        pass
