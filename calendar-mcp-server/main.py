#!/usr/bin/env python3
"""MCP Calendar Server - Basic implementation."""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="MCP Calendar Server", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

DB_PATH = Path(os.getenv("CALENDAR_DB_PATH", "calendar.db"))


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


@contextmanager
def get_db():
    """Get database connection with automatic commit/rollback."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize database schema."""
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bookings (
                booking_id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                date_iso TEXT NOT NULL,
                start_time_iso TEXT NOT NULL,
                end_time_iso TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'confirmed',
                created_at TEXT NOT NULL,
                confirmation_email_sent INTEGER NOT NULL DEFAULT 0,
                reminder_sent INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_bookings_customer_id ON bookings(customer_id)
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_bookings_date ON bookings(date_iso)
            """
        )


def get_default_slots(date_iso: str) -> list[dict]:
    """Generate default available slots for a date."""
    slots = []
    for hour in range(9, 18):
        start = f"{date_iso}T{hour:02d}:00:00Z"
        end = f"{date_iso}T{hour + 1:02d}:00:00Z"
        slots.append(
            {
                "date_iso": date_iso,
                "start_time_iso": start,
                "end_time_iso": end,
                "available": True,
            }
        )
    return slots


def check_availability_tool(date_iso: str, start_time_iso: str, end_time_iso: str) -> dict:
    """Check if a time slot is available."""
    with get_db() as conn:
        cursor = conn.execute(
            """
            SELECT COUNT(*) as count FROM bookings
            WHERE date_iso = ? 
            AND start_time_iso = ?
            AND end_time_iso = ?
            AND status IN ('pending', 'confirmed')
            """,
            (date_iso, start_time_iso, end_time_iso),
        )
        count = cursor.fetchone()["count"]
        return {"available": count == 0}


def get_available_slots_tool(date_iso: str) -> dict:
    """Get available slots for a date."""
    default_slots = get_default_slots(date_iso)
    with get_db() as conn:
        cursor = conn.execute(
            """
            SELECT start_time_iso, end_time_iso FROM bookings
            WHERE date_iso = ?
            AND status IN ('pending', 'confirmed')
            """,
            (date_iso,),
        )
        booked_slots = {(row["start_time_iso"], row["end_time_iso"]) for row in cursor.fetchall()}

    available_slots = []
    for slot in default_slots:
        if (slot["start_time_iso"], slot["end_time_iso"]) not in booked_slots:
            available_slots.append(slot)

    return {"slots": available_slots}


def create_booking_tool(
    customer_id: str,
    customer_name: str,
    date_iso: str,
    start_time_iso: str,
    end_time_iso: str,
) -> dict:
    """Create a new booking."""
    booking_id = f"BOOKING-{uuid.uuid4().hex[:8].upper()}"
    created_at = datetime.now(tz=timezone.utc).isoformat()

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO bookings (
                booking_id, customer_id, customer_name, date_iso,
                start_time_iso, end_time_iso, status, created_at,
                confirmation_email_sent, reminder_sent
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (booking_id, customer_id, customer_name, date_iso, start_time_iso, end_time_iso, "confirmed", created_at, 0, 0),
        )

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
        }
    }


def get_booking_tool(booking_id: str) -> dict:
    """Get a booking by ID."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM bookings WHERE booking_id = ?", (booking_id,))
        row = cursor.fetchone()
        if row is None:
            return {"booking": None}

        return {
            "booking": {
                "booking_id": row["booking_id"],
                "customer_id": row["customer_id"],
                "customer_name": row["customer_name"],
                "date_iso": row["date_iso"],
                "start_time_iso": row["start_time_iso"],
                "end_time_iso": row["end_time_iso"],
                "status": row["status"],
                "created_at": row["created_at"],
                "confirmation_email_sent": bool(row["confirmation_email_sent"]),
                "reminder_sent": bool(row["reminder_sent"]),
            }
        }


def list_bookings_tool(customer_id: str) -> dict:
    """List bookings for a customer."""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM bookings WHERE customer_id = ? ORDER BY created_at DESC",
            (customer_id,),
        )
        rows = cursor.fetchall()

    bookings = []
    for row in rows:
        bookings.append(
            {
                "booking_id": row["booking_id"],
                "customer_id": row["customer_id"],
                "customer_name": row["customer_name"],
                "date_iso": row["date_iso"],
                "start_time_iso": row["start_time_iso"],
                "end_time_iso": row["end_time_iso"],
                "status": row["status"],
                "created_at": row["created_at"],
                "confirmation_email_sent": bool(row["confirmation_email_sent"]),
                "reminder_sent": bool(row["reminder_sent"]),
            }
        )

    return {"bookings": bookings}


def update_booking_tool(
    booking_id: str,
    date_iso: str | None = None,
    start_time_iso: str | None = None,
    end_time_iso: str | None = None,
    status: str | None = None,
) -> dict:
    """Update a booking."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM bookings WHERE booking_id = ?", (booking_id,))
        row = cursor.fetchone()
        if row is None:
            return {"booking": None}

        updates = []
        params = []
        if date_iso is not None:
            updates.append("date_iso = ?")
            params.append(date_iso)
        if start_time_iso is not None:
            updates.append("start_time_iso = ?")
            params.append(start_time_iso)
        if end_time_iso is not None:
            updates.append("end_time_iso = ?")
            params.append(end_time_iso)
        if status is not None:
            updates.append("status = ?")
            params.append(status)

        if updates:
            params.append(booking_id)
            conn.execute(
                f"UPDATE bookings SET {', '.join(updates)} WHERE booking_id = ?",
                params,
            )

        cursor = conn.execute("SELECT * FROM bookings WHERE booking_id = ?", (booking_id,))
        row = cursor.fetchone()

        return {
            "booking": {
                "booking_id": row["booking_id"],
                "customer_id": row["customer_id"],
                "customer_name": row["customer_name"],
                "date_iso": row["date_iso"],
                "start_time_iso": row["start_time_iso"],
                "end_time_iso": row["end_time_iso"],
                "status": row["status"],
                "created_at": row["created_at"],
                "confirmation_email_sent": bool(row["confirmation_email_sent"]),
                "reminder_sent": bool(row["reminder_sent"]),
            }
        }


def delete_booking_tool(booking_id: str) -> dict:
    """Delete a booking."""
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM bookings WHERE booking_id = ?", (booking_id,))
        return {"success": cursor.rowcount > 0}


@app.on_event("startup")
def startup_event():
    """Initialize database on startup."""
    init_db()


@app.post("/mcp")
async def mcp_endpoint(request: MCPRequest):
    """Handle MCP JSON-RPC requests."""
    method = request.method
    params = request.params or {}

    try:
        if method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name == "check_availability":
                result = check_availability_tool(
                    date_iso=arguments["date_iso"],
                    start_time_iso=arguments["start_time_iso"],
                    end_time_iso=arguments["end_time_iso"],
                )
            elif tool_name == "get_available_slots":
                result = get_available_slots_tool(date_iso=arguments["date_iso"])
            elif tool_name == "create_booking":
                result = create_booking_tool(
                    customer_id=arguments["customer_id"],
                    customer_name=arguments["customer_name"],
                    date_iso=arguments["date_iso"],
                    start_time_iso=arguments["start_time_iso"],
                    end_time_iso=arguments["end_time_iso"],
                )
            elif tool_name == "get_booking":
                result = get_booking_tool(booking_id=arguments["booking_id"])
            elif tool_name == "list_bookings":
                result = list_bookings_tool(customer_id=arguments["customer_id"])
            elif tool_name == "update_booking":
                result = update_booking_tool(
                    booking_id=arguments["booking_id"],
                    date_iso=arguments.get("date_iso"),
                    start_time_iso=arguments.get("start_time_iso"),
                    end_time_iso=arguments.get("end_time_iso"),
                    status=arguments.get("status"),
                )
            elif tool_name == "delete_booking":
                result = delete_booking_tool(booking_id=arguments["booking_id"])
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
    return {"status": "ok", "service": "mcp-calendar-server"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("CALENDAR_SERVER_PORT", "60000"))
    uvicorn.run(app, host="0.0.0.0", port=port)

