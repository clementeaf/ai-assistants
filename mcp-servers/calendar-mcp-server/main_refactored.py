#!/usr/bin/env python3
"""MCP Calendar Server - Refactored to support multiple backends."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from calendar_mcp_server.backends import SQLiteBackend

try:
    from calendar_mcp_server.backends import GoogleCalendarBackend
except ImportError:
    GoogleCalendarBackend = None

app = FastAPI(title="MCP Calendar Server", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)


class MCPRequest(BaseModel):
    """MCP JSON-RPC request."""

    jsonrpc: str = "2.0"
    id: int | str
    method: str
    params: dict


class MCPResponse(BaseModel):
    """MCP JSON-RPC response."""

    jsonrpc: str = "2.0"
    id: int | str
    result: dict | None = None
    error: dict | None = None


def get_backend():
    """
    Get the configured calendar backend.
    @returns CalendarBackend instance
    """
    backend_type = os.getenv("CALENDAR_BACKEND", "sqlite").lower()

    if backend_type == "google_calendar":
        if GoogleCalendarBackend is None:
            raise ValueError(
                "Google Calendar backend not available. Install google-api-python-client and google-auth-httplib2"
            )

        service_account_file = os.getenv("GOOGLE_CALENDAR_SERVICE_ACCOUNT_FILE")
        calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")
        client_id = os.getenv("GOOGLE_CALENDAR_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET")
        refresh_token = os.getenv("GOOGLE_CALENDAR_REFRESH_TOKEN")

        return GoogleCalendarBackend(
            service_account_file=service_account_file,
            calendar_id=calendar_id,
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token,
        )
    else:
        db_path = Path(os.getenv("CALENDAR_DB_PATH", "calendar.db"))
        return SQLiteBackend(db_path=db_path)


backend = None


@app.on_event("startup")
def startup_event():
    """Initialize backend on startup."""
    global backend
    try:
        backend = get_backend()
    except Exception as e:
        print(f"Error initializing backend: {e}")
        raise


@app.post("/mcp")
async def mcp_endpoint(request: MCPRequest):
    """Handle MCP JSON-RPC requests."""
    global backend
    if backend is None:
        backend = get_backend()

    method = request.method
    params = request.params or {}

    try:
        if method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name == "check_availability":
                result = backend.check_availability(
                    date_iso=arguments["date_iso"],
                    start_time_iso=arguments["start_time_iso"],
                    end_time_iso=arguments["end_time_iso"],
                )
                result = {"available": result}
            elif tool_name == "get_available_slots":
                slots = backend.get_available_slots(date_iso=arguments["date_iso"])
                result = {"slots": slots}
            elif tool_name == "create_booking":
                booking_result = backend.create_booking(
                    customer_id=arguments["customer_id"],
                    customer_name=arguments["customer_name"],
                    date_iso=arguments["date_iso"],
                    start_time_iso=arguments["start_time_iso"],
                    end_time_iso=arguments["end_time_iso"],
                )
                result = booking_result
            elif tool_name == "get_booking":
                result = backend.get_booking(booking_id=arguments["booking_id"])
                if result is None:
                    result = {"booking": None}
            elif tool_name == "list_bookings":
                bookings_result = backend.list_bookings(customer_id=arguments["customer_id"])
                result = bookings_result
            elif tool_name == "update_booking":
                booking_result = backend.update_booking(
                    booking_id=arguments["booking_id"],
                    date_iso=arguments.get("date_iso"),
                    start_time_iso=arguments.get("start_time_iso"),
                    end_time_iso=arguments.get("end_time_iso"),
                    status=arguments.get("status"),
                )
                result = booking_result if booking_result is not None else {"booking": None}
            elif tool_name == "delete_booking":
                success = backend.delete_booking(booking_id=arguments["booking_id"])
                result = {"success": success}
            else:
                return MCPResponse(
                    id=request.id,
                    error={"code": -32601, "message": f"Unknown tool: {tool_name}"},
                )

            return MCPResponse(id=request.id, result=result)
        else:
            return MCPResponse(
                id=request.id,
                error={"code": -32601, "message": f"Unknown method: {method}"},
            )
    except KeyError as e:
        return MCPResponse(
            id=request.id,
            error={"code": -32602, "message": f"Missing parameter: {e}"},
        )
    except Exception as e:
        return MCPResponse(
            id=request.id,
            error={"code": -32603, "message": f"Internal error: {str(e)}"},
        )


@app.get("/health")
async def health():
    """Health check endpoint."""
    backend_type = os.getenv("CALENDAR_BACKEND", "sqlite")
    return {"status": "ok", "service": "mcp-calendar-server", "backend": backend_type}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("CALENDAR_SERVER_PORT", "60000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
