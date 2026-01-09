from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from ai_assistants.adapters.booking_log import BookingLogAdapter
from ai_assistants.domain.booking_log.models import BookingLog


class MCPBookingLogAdapter(BookingLogAdapter):
    """Adapter that connects to a booking log service via MCP (Model Context Protocol)."""

    def __init__(self, mcp_server_url: str, api_key: str | None = None, timeout_seconds: float = 10.0) -> None:
        self._mcp_url = mcp_server_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout_seconds
        self._client = httpx.Client(timeout=timeout_seconds)

    def _call_mcp_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call an MCP tool and return the result."""
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

    def _parse_datetime(self, dt_str: str | None) -> datetime:
        """Parse datetime string to datetime object."""
        if dt_str is None:
            return datetime.now()
        if isinstance(dt_str, str):
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return datetime.now()

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
        args: dict[str, Any] = {
            "booking_code": booking_code,
            "customer_name": customer_name,
        }
        if customer_id is not None:
            args["customer_id"] = customer_id
        if date_iso is not None:
            args["date_iso"] = date_iso
        if time_iso is not None:
            args["time_iso"] = time_iso
        if area_id is not None:
            args["area_id"] = area_id
        if area_name is not None:
            args["area_name"] = area_name
        if specialty_id is not None:
            args["specialty_id"] = specialty_id
        if specialty_name is not None:
            args["specialty_name"] = specialty_name
        if professional_id is not None:
            args["professional_id"] = professional_id
        if professional_name is not None:
            args["professional_name"] = professional_name
        if observations is not None:
            args["observations"] = observations

        result = self._call_mcp_tool("create_booking_log", args)
        log_data = result.get("log", {})
        return BookingLog(
            log_id=log_data["log_id"],
            booking_code=log_data["booking_code"],
            customer_name=log_data["customer_name"],
            customer_id=log_data.get("customer_id"),
            date_iso=log_data["date_iso"],
            time_iso=log_data["time_iso"],
            area_id=log_data.get("area_id"),
            area_name=log_data.get("area_name"),
            specialty_id=log_data.get("specialty_id"),
            specialty_name=log_data.get("specialty_name"),
            professional_id=log_data.get("professional_id"),
            professional_name=log_data.get("professional_name"),
            observations=log_data.get("observations"),
            created_at=self._parse_datetime(log_data.get("created_at")),
            updated_at=self._parse_datetime(log_data.get("updated_at")),
        )

    def get_booking_log(self, booking_code: str | None = None, log_id: str | None = None) -> BookingLog | None:
        """Get a booking log by booking code or log ID."""
        args: dict[str, Any] = {}
        if booking_code is not None:
            args["booking_code"] = booking_code
        if log_id is not None:
            args["log_id"] = log_id
        result = self._call_mcp_tool("get_booking_log", args)
        log_data = result.get("log")
        if log_data is None:
            return None
        return BookingLog(
            log_id=log_data["log_id"],
            booking_code=log_data["booking_code"],
            customer_name=log_data["customer_name"],
            customer_id=log_data.get("customer_id"),
            date_iso=log_data["date_iso"],
            time_iso=log_data["time_iso"],
            area_id=log_data.get("area_id"),
            area_name=log_data.get("area_name"),
            specialty_id=log_data.get("specialty_id"),
            specialty_name=log_data.get("specialty_name"),
            professional_id=log_data.get("professional_id"),
            professional_name=log_data.get("professional_name"),
            observations=log_data.get("observations"),
            created_at=self._parse_datetime(log_data.get("created_at")),
            updated_at=self._parse_datetime(log_data.get("updated_at")),
        )

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
        args: dict[str, Any] = {"limit": limit}
        if customer_id is not None:
            args["customer_id"] = customer_id
        if customer_name is not None:
            args["customer_name"] = customer_name
        if date_iso is not None:
            args["date_iso"] = date_iso
        if professional_id is not None:
            args["professional_id"] = professional_id
        if specialty_id is not None:
            args["specialty_id"] = specialty_id
        if area_id is not None:
            args["area_id"] = area_id

        result = self._call_mcp_tool("list_booking_logs", args)
        logs_data = result.get("logs", [])
        return [
            BookingLog(
                log_id=log["log_id"],
                booking_code=log["booking_code"],
                customer_name=log["customer_name"],
                customer_id=log.get("customer_id"),
                date_iso=log["date_iso"],
                time_iso=log["time_iso"],
                area_id=log.get("area_id"),
                area_name=log.get("area_name"),
                specialty_id=log.get("specialty_id"),
                specialty_name=log.get("specialty_name"),
                professional_id=log.get("professional_id"),
                professional_name=log.get("professional_name"),
                observations=log.get("observations"),
                created_at=self._parse_datetime(log.get("created_at")),
                updated_at=self._parse_datetime(log.get("updated_at")),
            )
            for log in logs_data
        ]

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
        args: dict[str, Any] = {}
        if booking_code is not None:
            args["booking_code"] = booking_code
        if log_id is not None:
            args["log_id"] = log_id
        if customer_name is not None:
            args["customer_name"] = customer_name
        if date_iso is not None:
            args["date_iso"] = date_iso
        if time_iso is not None:
            args["time_iso"] = time_iso
        if area_id is not None:
            args["area_id"] = area_id
        if area_name is not None:
            args["area_name"] = area_name
        if specialty_id is not None:
            args["specialty_id"] = specialty_id
        if specialty_name is not None:
            args["specialty_name"] = specialty_name
        if professional_id is not None:
            args["professional_id"] = professional_id
        if professional_name is not None:
            args["professional_name"] = professional_name
        if observations is not None:
            args["observations"] = observations

        result = self._call_mcp_tool("update_booking_log", args)
        log_data = result.get("log")
        if log_data is None:
            return None
        return BookingLog(
            log_id=log_data["log_id"],
            booking_code=log_data["booking_code"],
            customer_name=log_data["customer_name"],
            customer_id=log_data.get("customer_id"),
            date_iso=log_data["date_iso"],
            time_iso=log_data["time_iso"],
            area_id=log_data.get("area_id"),
            area_name=log_data.get("area_name"),
            specialty_id=log_data.get("specialty_id"),
            specialty_name=log_data.get("specialty_name"),
            professional_id=log_data.get("professional_id"),
            professional_name=log_data.get("professional_name"),
            observations=log_data.get("observations"),
            created_at=self._parse_datetime(log_data.get("created_at")),
            updated_at=self._parse_datetime(log_data.get("updated_at")),
        )

    def delete_booking_log(self, booking_code: str | None = None, log_id: str | None = None) -> bool:
        """Delete a booking log entry."""
        args: dict[str, Any] = {}
        if booking_code is not None:
            args["booking_code"] = booking_code
        if log_id is not None:
            args["log_id"] = log_id
        result = self._call_mcp_tool("delete_booking_log", args)
        return result.get("success", False)

