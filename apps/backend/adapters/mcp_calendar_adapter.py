from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import httpx

from ai_assistants.adapters.bookings import BookingsAdapter
from ai_assistants.domain.bookings.models import Booking, BookingSlot, BookingStatus


class MCPCalendarAdapter(BookingsAdapter):
    """Adapter that connects to a calendar service via MCP (Model Context Protocol)."""

    def __init__(self, mcp_server_url: str, api_key: str | None = None, timeout_seconds: float = 10.0) -> None:
        self._mcp_url = mcp_server_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout_seconds
        self._client = httpx.Client(timeout=timeout_seconds)

    def _call_mcp_tool(self, tool_name: str, arguments: dict[str, Any], customer_id: str | None = None) -> dict[str, Any]:
        """
        Call an MCP tool and return the result.
        
        @param tool_name - Name of the MCP tool to call
        @param arguments - Tool arguments
        @param customer_id - Optional customer_id to pass to MCP (for multi-user calendar support)
        """
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
        }
        
        # Si hay customer_id, agregarlo como header para que el MCP Server sepa qué calendario usar
        if customer_id:
            headers["X-Customer-Id"] = customer_id

        response = self._client.post(
            f"{self._mcp_url}/mcp",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        json_response = response.json()
        if "error" in json_response and json_response["error"] is not None:
            error_msg = json_response["error"].get("message", "Unknown error")
            raise ValueError(f"MCP error: {error_msg}")
        return json_response.get("result", {})

    def check_availability(self, date_iso: str, start_time_iso: str, end_time_iso: str, customer_id: str | None = None) -> bool:
        """Check if a time slot is available for booking."""
        result = self._call_mcp_tool(
            "check_availability",
            {
                "date_iso": date_iso,
                "start_time_iso": start_time_iso,
                "end_time_iso": end_time_iso,
            },
            customer_id=customer_id,
        )
        return result.get("available", False)

    def get_available_slots(self, date_iso: str, customer_id: str | None = None) -> list[BookingSlot]:
        """Return available booking slots for a given date."""
        result = self._call_mcp_tool("get_available_slots", {"date_iso": date_iso}, customer_id=customer_id)
        slots_data = result.get("slots", [])
        return [
            BookingSlot(
                date_iso=slot["date_iso"],
                start_time_iso=slot["start_time_iso"],
                end_time_iso=slot["end_time_iso"],
                available=slot["available"],
            )
            for slot in slots_data
        ]

    def create_booking(
        self,
        customer_id: str,
        customer_name: str,
        date_iso: str,
        start_time_iso: str,
        end_time_iso: str,
    ) -> Booking:
        """Create a new booking and return it."""
        result = self._call_mcp_tool(
            "create_booking",
            {
                "customer_id": customer_id,
                "customer_name": customer_name,
                "date_iso": date_iso,
                "start_time_iso": start_time_iso,
                "end_time_iso": end_time_iso,
            },
            customer_id=customer_id,
        )
        booking_data = result.get("booking", {})
        created_at_str = booking_data.get("created_at")
        if isinstance(created_at_str, str):
            created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        else:
            created_at = datetime.now()
        return Booking(
            booking_id=booking_data["booking_id"],
            customer_id=booking_data["customer_id"],
            customer_name=booking_data["customer_name"],
            date_iso=booking_data["date_iso"],
            start_time_iso=booking_data["start_time_iso"],
            end_time_iso=booking_data["end_time_iso"],
            status=BookingStatus(booking_data["status"]),
            created_at=created_at,
            confirmation_email_sent=booking_data.get("confirmation_email_sent", False),
            reminder_sent=booking_data.get("reminder_sent", False),
        )

    def get_booking(self, booking_id: str, customer_id: str | None = None) -> Booking | None:
        """Return a booking by id, or None if not found."""
        result = self._call_mcp_tool("get_booking", {"booking_id": booking_id}, customer_id=customer_id)
        booking_data = result.get("booking")
        if booking_data is None:
            return None
        created_at_str = booking_data.get("created_at")
        if isinstance(created_at_str, str):
            created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        else:
            created_at = datetime.now()
        return Booking(
            booking_id=booking_data["booking_id"],
            customer_id=booking_data["customer_id"],
            customer_name=booking_data["customer_name"],
            date_iso=booking_data["date_iso"],
            start_time_iso=booking_data["start_time_iso"],
            end_time_iso=booking_data["end_time_iso"],
            status=BookingStatus(booking_data["status"]),
            created_at=created_at,
            confirmation_email_sent=booking_data.get("confirmation_email_sent", False),
            reminder_sent=booking_data.get("reminder_sent", False),
        )

    def list_bookings(self, customer_id: str) -> list[Booking]:
        """Return bookings for the given customer id."""
        result = self._call_mcp_tool("list_bookings", {"customer_id": customer_id}, customer_id=customer_id)
        bookings_data = result.get("bookings", [])
        bookings = []
        for b in bookings_data:
            created_at_str = b.get("created_at")
            if isinstance(created_at_str, str):
                created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            else:
                created_at = datetime.now()
            bookings.append(
                Booking(
                    booking_id=b["booking_id"],
                    customer_id=b["customer_id"],
                    customer_name=b["customer_name"],
                    date_iso=b["date_iso"],
                    start_time_iso=b["start_time_iso"],
                    end_time_iso=b["end_time_iso"],
                    status=BookingStatus(b["status"]),
                    created_at=created_at,
                    confirmation_email_sent=b.get("confirmation_email_sent", False),
                    reminder_sent=b.get("reminder_sent", False),
                )
            )
        return bookings

    def update_booking(
        self,
        booking_id: str,
        date_iso: str | None = None,
        start_time_iso: str | None = None,
        end_time_iso: str | None = None,
        status: str | None = None,
        customer_id: str | None = None,
    ) -> Booking | None:
        """Update an existing booking. Returns the updated booking or None if not found."""
        args: dict[str, Any] = {"booking_id": booking_id}
        if date_iso is not None:
            args["date_iso"] = date_iso
        if start_time_iso is not None:
            args["start_time_iso"] = start_time_iso
        if end_time_iso is not None:
            args["end_time_iso"] = end_time_iso
        if status is not None:
            args["status"] = status

        result = self._call_mcp_tool("update_booking", args, customer_id=customer_id)
        booking_data = result.get("booking")
        if booking_data is None:
            return None
        created_at_str = booking_data.get("created_at")
        if isinstance(created_at_str, str):
            created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        else:
            created_at = datetime.now()
        return Booking(
            booking_id=booking_data["booking_id"],
            customer_id=booking_data["customer_id"],
            customer_name=booking_data["customer_name"],
            date_iso=booking_data["date_iso"],
            start_time_iso=booking_data["start_time_iso"],
            end_time_iso=booking_data["end_time_iso"],
            status=BookingStatus(booking_data["status"]),
            created_at=created_at,
            confirmation_email_sent=booking_data.get("confirmation_email_sent", False),
            reminder_sent=booking_data.get("reminder_sent", False),
        )

    def delete_booking(self, booking_id: str, customer_id: str | None = None) -> bool:
        """Delete a booking. Returns True if deleted, False if not found."""
        result = self._call_mcp_tool("delete_booking", {"booking_id": booking_id}, customer_id=customer_id)
        return result.get("success", False)

