"""Google Calendar backend implementation for calendar storage."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from calendar_mcp_server.backends.base import CalendarBackend

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class GoogleCalendarBackend(CalendarBackend):
    """Google Calendar-based backend using Google Calendar API with multi-user support."""

    def __init__(
        self,
        oauth2_handler: Any | None = None,
        service_account_file: str | None = None,
        calendar_id: str = "primary",
        client_id: str | None = None,
        client_secret: str | None = None,
        refresh_token: str | None = None,
    ) -> None:
        """
        Initialize Google Calendar backend.
        @param oauth2_handler - OAuth2Handler instance for multi-user support (preferred)
        @param service_account_file - Path to service account JSON file (legacy)
        @param calendar_id - Google Calendar ID (default: 'primary')
        @param client_id - OAuth2 client ID (legacy)
        @param client_secret - OAuth2 client secret (legacy)
        @param refresh_token - OAuth2 refresh token (legacy)
        """
        self._oauth2_handler = oauth2_handler
        self._calendar_id = calendar_id
        self._legacy_service = None
        
        if not oauth2_handler:
            self._legacy_service = self._build_service(service_account_file, client_id, client_secret, refresh_token)

    def _build_service(
        self,
        service_account_file: str | None,
        client_id: str | None,
        client_secret: str | None,
        refresh_token: str | None,
    ) -> Any:
        """
        Build Google Calendar service with appropriate authentication.
        @param service_account_file - Path to service account JSON
        @param client_id - OAuth2 client ID
        @param client_secret - OAuth2 client secret
        @param refresh_token - OAuth2 refresh token
        @returns Google Calendar service instance
        """
        creds = None

        if service_account_file and os.path.exists(service_account_file):
            creds = service_account.Credentials.from_service_account_file(service_account_file, scopes=SCOPES)
        elif client_id and client_secret and refresh_token:
            creds = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id,
                client_secret=client_secret,
                scopes=SCOPES,
            )
            creds.refresh(Request())
        else:
            raise ValueError(
                "Either service_account_file or (client_id, client_secret, refresh_token) must be provided"
            )

        return build("calendar", "v3", credentials=creds)

    def _parse_datetime(self, iso_string: str) -> datetime:
        """
        Parse ISO datetime string to datetime object.
        @param iso_string - ISO format datetime string
        @returns Datetime object
        """
        if iso_string.endswith("Z"):
            iso_string = iso_string[:-1] + "+00:00"
        return datetime.fromisoformat(iso_string)

    def _format_datetime(self, dt: datetime) -> str:
        """
        Format datetime to RFC3339 string for Google Calendar API.
        @param dt - Datetime object
        @returns RFC3339 formatted string
        """
        return dt.isoformat()

    def _get_default_slots(self, date_iso: str) -> list[dict[str, Any]]:
        """
        Generate default available slots for a date.
        @param date_iso - Date in ISO format (YYYY-MM-DD)
        @returns List of default slots
        """
        slots = []
        date_obj = datetime.fromisoformat(date_iso).replace(tzinfo=timezone.utc)
        for hour in range(9, 18):
            start = date_obj.replace(hour=hour, minute=0, second=0, microsecond=0)
            end = start.replace(hour=hour + 1)
            slots.append(
                {
                    "date_iso": date_iso,
                    "start_time_iso": start.isoformat(),
                    "end_time_iso": end.isoformat(),
                    "available": True,
                }
            )
        return slots

    def _get_service(self, customer_id: str | None = None) -> Any:
        """
        Get Google Calendar service for a customer.
        @param customer_id - Customer identifier (for multi-user mode)
        @returns Google Calendar service instance
        """
        if self._oauth2_handler and customer_id:
            credentials = self._oauth2_handler.get_credentials(customer_id)
            if credentials:
                return build("calendar", "v3", credentials=credentials)
            raise ValueError(f"Google Calendar not connected for customer: {customer_id}")
        
        if self._legacy_service:
            return self._legacy_service
        
        raise ValueError("No authentication configured for Google Calendar")

    def check_availability(self, date_iso: str, start_time_iso: str, end_time_iso: str, customer_id: str | None = None) -> bool:
        """
        Check if a time slot is available for booking.
        @param date_iso - Date in ISO format (YYYY-MM-DD)
        @param start_time_iso - Start time in ISO format
        @param end_time_iso - End time in ISO format
        @param customer_id - Customer identifier (for multi-user mode)
        @returns True if available, False otherwise
        """
        try:
            service = self._get_service(customer_id)
            start_dt = self._parse_datetime(start_time_iso)
            end_dt = self._parse_datetime(end_time_iso)

            events_result = (
                service.events()
                .list(
                    calendarId=self._calendar_id,
                    timeMin=self._format_datetime(start_dt),
                    timeMax=self._format_datetime(end_dt),
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])
            return len(events) == 0
        except HttpError as e:
            raise ValueError(f"Error checking availability: {e}")

    def get_available_slots(self, date_iso: str, customer_id: str | None = None) -> list[dict[str, Any]]:
        """
        Get available slots for a date.
        @param date_iso - Date in ISO format (YYYY-MM-DD)
        @param customer_id - Customer identifier (for multi-user mode)
        @returns List of available slots
        """
        service = self._get_service(customer_id)
        default_slots = self._get_default_slots(date_iso)
        date_obj = datetime.fromisoformat(date_iso).replace(tzinfo=timezone.utc)
        time_min = date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
        time_max = date_obj.replace(hour=23, minute=59, second=59, microsecond=999999)

        try:
            events_result = (
                service.events()
                .list(
                    calendarId=self._calendar_id,
                    timeMin=self._format_datetime(time_min),
                    timeMax=self._format_datetime(time_max),
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])
            booked_slots = set()
            for event in events:
                start = event["start"].get("dateTime", event["start"].get("date"))
                end = event["end"].get("dateTime", event["end"].get("date"))
                booked_slots.add((start, end))

            available_slots = []
            for slot in default_slots:
                slot_start = slot["start_time_iso"]
                slot_end = slot["end_time_iso"]
                if (slot_start, slot_end) not in booked_slots:
                    available_slots.append(slot)

            return available_slots
        except HttpError as e:
            raise ValueError(f"Error getting available slots: {e}")

    def create_booking(
        self,
        customer_id: str,
        customer_name: str,
        date_iso: str,
        start_time_iso: str,
        end_time_iso: str,
    ) -> dict[str, Any]:
        """
        Create a new booking in Google Calendar.
        @param customer_id - Customer identifier (also used for OAuth2 lookup)
        @param customer_name - Customer name
        @param date_iso - Date in ISO format (YYYY-MM-DD)
        @param start_time_iso - Start time in ISO format
        @param end_time_iso - End time in ISO format
        @returns Booking dictionary
        """
        service = self._get_service(customer_id)
        booking_id = f"BOOKING-{uuid.uuid4().hex[:8].upper()}"
        created_at = datetime.now(tz=timezone.utc).isoformat()

        start_dt = self._parse_datetime(start_time_iso)
        end_dt = self._parse_datetime(end_time_iso)

        event = {
            "summary": f"Reserva: {customer_name}",
            "description": f"Cliente: {customer_name}\nID Cliente: {customer_id}\nID Reserva: {booking_id}",
            "start": {
                "dateTime": self._format_datetime(start_dt),
                "timeZone": "UTC",
            },
            "end": {
                "dateTime": self._format_datetime(end_dt),
                "timeZone": "UTC",
            },
            "extendedProperties": {
                "private": {
                    "booking_id": booking_id,
                    "customer_id": customer_id,
                    "customer_name": customer_name,
                }
            },
        }

        try:
            created_event = service.events().insert(calendarId=self._calendar_id, body=event).execute()
            event_id = created_event.get("id")

            return {
                "booking": {
                    "booking_id": booking_id,
                    "customer_id": customer_id,
                    "customer_name": customer_name,
                    "date_iso": date_iso,
                    "start_time_iso": start_time_iso,
                    "end_time_iso": end_time_iso,
                    "status": "confirmed",
                    "created_at": created_at,
                    "confirmation_email_sent": False,
                    "reminder_sent": False,
                    "google_event_id": event_id,
                }
            }
        except HttpError as e:
            raise ValueError(f"Error creating booking: {e}")

    def get_booking(self, booking_id: str, customer_id: str | None = None) -> dict[str, Any] | None:
        """
        Get a booking by ID from Google Calendar.
        @param booking_id - Booking identifier
        @param customer_id - Customer identifier (for multi-user mode)
        @returns Booking dictionary or None if not found
        """
        service = self._get_service(customer_id)
        try:
            events_result = (
                service.events()
                .list(
                    calendarId=self._calendar_id,
                    privateExtendedProperty=f"booking_id={booking_id}",
                )
                .execute()
            )

            events = events_result.get("items", [])
            if not events:
                return None

            event = events[0]
            extended_props = event.get("extendedProperties", {}).get("private", {})
            start = event["start"].get("dateTime", event["start"].get("date"))
            end = event["end"].get("dateTime", event["end"].get("date"))

            start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))

            return {
                "booking": {
                    "booking_id": extended_props.get("booking_id", booking_id),
                    "customer_id": extended_props.get("customer_id", ""),
                    "customer_name": extended_props.get("customer_name", event.get("summary", "")),
                    "date_iso": start_dt.date().isoformat(),
                    "start_time_iso": start_dt.isoformat(),
                    "end_time_iso": end_dt.isoformat(),
                    "status": "confirmed" if event.get("status") == "confirmed" else "pending",
                    "created_at": event.get("created", datetime.now(tz=timezone.utc).isoformat()),
                    "confirmation_email_sent": False,
                    "reminder_sent": False,
                    "google_event_id": event.get("id"),
                }
            }
        except HttpError as e:
            raise ValueError(f"Error getting booking: {e}")

    def list_bookings(self, customer_id: str) -> list[dict[str, Any]]:
        """
        List bookings for a customer from Google Calendar.
        @param customer_id - Customer identifier (also used for OAuth2 lookup)
        @returns List of booking dictionaries
        """
        service = self._get_service(customer_id)
        try:
            events_result = (
                service.events()
                .list(
                    calendarId=self._calendar_id,
                    privateExtendedProperty=f"customer_id={customer_id}",
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])
            bookings = []

            for event in events:
                extended_props = event.get("extendedProperties", {}).get("private", {})
                start = event["start"].get("dateTime", event["start"].get("date"))
                end = event["end"].get("dateTime", event["end"].get("date"))

                start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))

                bookings.append(
                    {
                        "booking_id": extended_props.get("booking_id", ""),
                        "customer_id": extended_props.get("customer_id", customer_id),
                        "customer_name": extended_props.get("customer_name", event.get("summary", "")),
                        "date_iso": start_dt.date().isoformat(),
                        "start_time_iso": start_dt.isoformat(),
                        "end_time_iso": end_dt.isoformat(),
                        "status": "confirmed" if event.get("status") == "confirmed" else "pending",
                        "created_at": event.get("created", datetime.now(tz=timezone.utc).isoformat()),
                        "confirmation_email_sent": False,
                        "reminder_sent": False,
                        "google_event_id": event.get("id"),
                    }
                )

            return {"bookings": bookings}
        except HttpError as e:
            raise ValueError(f"Error listing bookings: {e}")

    def update_booking(
        self,
        booking_id: str,
        date_iso: str | None = None,
        start_time_iso: str | None = None,
        end_time_iso: str | None = None,
        status: str | None = None,
        customer_id: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Update an existing booking in Google Calendar.
        @param booking_id - Booking identifier
        @param date_iso - New date (optional)
        @param start_time_iso - New start time (optional)
        @param end_time_iso - New end time (optional)
        @param status - New status (optional)
        @param customer_id - Customer identifier (for multi-user mode)
        @returns Updated booking dictionary or None if not found
        """
        service = self._get_service(customer_id)
        try:
            events_result = (
                service.events()
                .list(
                    calendarId=self._calendar_id,
                    privateExtendedProperty=f"booking_id={booking_id}",
                )
                .execute()
            )

            events = events_result.get("items", [])
            if not events:
                return None

            event = events[0]
            event_id = event["id"]

            if start_time_iso:
                start_dt = self._parse_datetime(start_time_iso)
                event["start"] = {
                    "dateTime": self._format_datetime(start_dt),
                    "timeZone": "UTC",
                }

            if end_time_iso:
                end_dt = self._parse_datetime(end_time_iso)
                event["end"] = {
                    "dateTime": self._format_datetime(end_dt),
                    "timeZone": "UTC",
                }

            if status:
                event["status"] = status

            updated_event = service.events().update(calendarId=self._calendar_id, eventId=event_id, body=event).execute()

            extended_props = updated_event.get("extendedProperties", {}).get("private", {})
            start = updated_event["start"].get("dateTime", updated_event["start"].get("date"))
            end = updated_event["end"].get("dateTime", updated_event["end"].get("date"))

            start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))

            return {
                "booking": {
                    "booking_id": extended_props.get("booking_id", booking_id),
                    "customer_id": extended_props.get("customer_id", ""),
                    "customer_name": extended_props.get("customer_name", updated_event.get("summary", "")),
                    "date_iso": start_dt.date().isoformat(),
                    "start_time_iso": start_dt.isoformat(),
                    "end_time_iso": end_dt.isoformat(),
                    "status": updated_event.get("status", "confirmed"),
                    "created_at": updated_event.get("created", datetime.now(tz=timezone.utc).isoformat()),
                    "confirmation_email_sent": False,
                    "reminder_sent": False,
                    "google_event_id": updated_event.get("id"),
                }
            }
        except HttpError as e:
            raise ValueError(f"Error updating booking: {e}")

    def delete_booking(self, booking_id: str, customer_id: str | None = None) -> bool:
        """
        Delete a booking from Google Calendar.
        @param booking_id - Booking identifier
        @param customer_id - Customer identifier (for multi-user mode)
        @returns True if deleted, False if not found
        """
        service = self._get_service(customer_id)
        try:
            events_result = (
                service.events()
                .list(
                    calendarId=self._calendar_id,
                    privateExtendedProperty=f"booking_id={booking_id}",
                )
                .execute()
            )

            events = events_result.get("items", [])
            if not events:
                return False

            event_id = events[0]["id"]
            service.events().delete(calendarId=self._calendar_id, eventId=event_id).execute()
            return True
        except HttpError as e:
            raise ValueError(f"Error deleting booking: {e}")
