#!/usr/bin/env python3
"""MCP Booking Log Server - Logbook/agenda for booking records."""

from __future__ import annotations

import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="MCP Booking Log Server", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = Path(os.getenv("BOOKING_LOG_DB_PATH", "booking_log.db"))


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
            CREATE TABLE IF NOT EXISTS booking_logs (
                log_id TEXT PRIMARY KEY,
                booking_code TEXT NOT NULL UNIQUE,
                customer_name TEXT NOT NULL,
                customer_id TEXT,
                date_iso TEXT NOT NULL,
                time_iso TEXT NOT NULL,
                area_id TEXT,
                area_name TEXT,
                specialty_id TEXT,
                specialty_name TEXT,
                professional_id TEXT,
                professional_name TEXT,
                observations TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_booking_code ON booking_logs(booking_code)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_customer_id ON booking_logs(customer_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_date ON booking_logs(date_iso)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_professional ON booking_logs(professional_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_specialty ON booking_logs(specialty_id)")


def create_booking_log_tool(
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
) -> dict:
    """Create a new booking log entry."""
    log_id = f"LOG-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(tz=timezone.utc).isoformat()

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO booking_logs (
                log_id, booking_code, customer_name, customer_id,
                date_iso, time_iso, area_id, area_name,
                specialty_id, specialty_name, professional_id, professional_name,
                observations, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                log_id,
                booking_code,
                customer_name,
                customer_id,
                date_iso,
                time_iso,
                area_id,
                area_name,
                specialty_id,
                specialty_name,
                professional_id,
                professional_name,
                observations or "",
                now,
                now,
            ),
        )

    return {
        "log": {
            "log_id": log_id,
            "booking_code": booking_code,
            "customer_name": customer_name,
            "customer_id": customer_id,
            "date_iso": date_iso,
            "time_iso": time_iso,
            "area_id": area_id,
            "area_name": area_name,
            "specialty_id": specialty_id,
            "specialty_name": specialty_name,
            "professional_id": professional_id,
            "professional_name": professional_name,
            "observations": observations,
            "created_at": now,
            "updated_at": now,
        }
    }


def get_booking_log_tool(booking_code: str | None = None, log_id: str | None = None) -> dict:
    """Get a booking log by booking code or log ID."""
    with get_db() as conn:
        if booking_code:
            cursor = conn.execute("SELECT * FROM booking_logs WHERE booking_code = ?", (booking_code,))
        elif log_id:
            cursor = conn.execute("SELECT * FROM booking_logs WHERE log_id = ?", (log_id,))
        else:
            return {"log": None}
        row = cursor.fetchone()
        if row is None:
            return {"log": None}

        return {
            "log": {
                "log_id": row["log_id"],
                "booking_code": row["booking_code"],
                "customer_name": row["customer_name"],
                "customer_id": row["customer_id"],
                "date_iso": row["date_iso"],
                "time_iso": row["time_iso"],
                "area_id": row["area_id"],
                "area_name": row["area_name"],
                "specialty_id": row["specialty_id"],
                "specialty_name": row["specialty_name"],
                "professional_id": row["professional_id"],
                "professional_name": row["professional_name"],
                "observations": row["observations"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        }


def list_booking_logs_tool(
    customer_id: str | None = None,
    customer_name: str | None = None,
    date_iso: str | None = None,
    professional_id: str | None = None,
    specialty_id: str | None = None,
    area_id: str | None = None,
    limit: int = 100,
) -> dict:
    """List booking logs with optional filters."""
    with get_db() as conn:
        conditions = []
        params = []
        if customer_id:
            conditions.append("customer_id = ?")
            params.append(customer_id)
        if customer_name:
            conditions.append("customer_name LIKE ?")
            params.append(f"%{customer_name}%")
        if date_iso:
            conditions.append("date_iso = ?")
            params.append(date_iso)
        if professional_id:
            conditions.append("professional_id = ?")
            params.append(professional_id)
        if specialty_id:
            conditions.append("specialty_id = ?")
            params.append(specialty_id)
        if area_id:
            conditions.append("area_id = ?")
            params.append(area_id)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.append(limit)
        query = f"SELECT * FROM booking_logs {where_clause} ORDER BY date_iso DESC, time_iso DESC LIMIT ?"
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()

    logs = [
        {
            "log_id": row["log_id"],
            "booking_code": row["booking_code"],
            "customer_name": row["customer_name"],
            "customer_id": row["customer_id"],
            "date_iso": row["date_iso"],
            "time_iso": row["time_iso"],
            "area_id": row["area_id"],
            "area_name": row["area_name"],
            "specialty_id": row["specialty_id"],
            "specialty_name": row["specialty_name"],
            "professional_id": row["professional_id"],
            "professional_name": row["professional_name"],
            "observations": row["observations"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        for row in rows
    ]

    return {"logs": logs, "count": len(logs)}


def update_booking_log_tool(
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
) -> dict:
    """Update a booking log entry."""
    with get_db() as conn:
        if booking_code:
            cursor = conn.execute("SELECT * FROM booking_logs WHERE booking_code = ?", (booking_code,))
        elif log_id:
            cursor = conn.execute("SELECT * FROM booking_logs WHERE log_id = ?", (log_id,))
        else:
            return {"log": None}
        row = cursor.fetchone()
        if row is None:
            return {"log": None}

        updates = []
        params = []
        if customer_name is not None:
            updates.append("customer_name = ?")
            params.append(customer_name)
        if date_iso is not None:
            updates.append("date_iso = ?")
            params.append(date_iso)
        if time_iso is not None:
            updates.append("time_iso = ?")
            params.append(time_iso)
        if area_id is not None:
            updates.append("area_id = ?")
            params.append(area_id)
        if area_name is not None:
            updates.append("area_name = ?")
            params.append(area_name)
        if specialty_id is not None:
            updates.append("specialty_id = ?")
            params.append(specialty_id)
        if specialty_name is not None:
            updates.append("specialty_name = ?")
            params.append(specialty_name)
        if professional_id is not None:
            updates.append("professional_id = ?")
            params.append(professional_id)
        if professional_name is not None:
            updates.append("professional_name = ?")
            params.append(professional_name)
        if observations is not None:
            updates.append("observations = ?")
            params.append(observations)

        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.now(tz=timezone.utc).isoformat())
            if booking_code:
                params.append(booking_code)
                conn.execute(f"UPDATE booking_logs SET {', '.join(updates)} WHERE booking_code = ?", params)
            else:
                params.append(log_id)
                conn.execute(f"UPDATE booking_logs SET {', '.join(updates)} WHERE log_id = ?", params)

        if booking_code:
            cursor = conn.execute("SELECT * FROM booking_logs WHERE booking_code = ?", (booking_code,))
        else:
            cursor = conn.execute("SELECT * FROM booking_logs WHERE log_id = ?", (log_id,))
        row = cursor.fetchone()

        return {
            "log": {
                "log_id": row["log_id"],
                "booking_code": row["booking_code"],
                "customer_name": row["customer_name"],
                "customer_id": row["customer_id"],
                "date_iso": row["date_iso"],
                "time_iso": row["time_iso"],
                "area_id": row["area_id"],
                "area_name": row["area_name"],
                "specialty_id": row["specialty_id"],
                "specialty_name": row["specialty_name"],
                "professional_id": row["professional_id"],
                "professional_name": row["professional_name"],
                "observations": row["observations"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        }


def delete_booking_log_tool(booking_code: str | None = None, log_id: str | None = None) -> dict:
    """Delete a booking log entry."""
    with get_db() as conn:
        if booking_code:
            cursor = conn.execute("DELETE FROM booking_logs WHERE booking_code = ?", (booking_code,))
        elif log_id:
            cursor = conn.execute("DELETE FROM booking_logs WHERE log_id = ?", (log_id,))
        else:
            return {"success": False}
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

            if tool_name == "create_booking_log":
                result = create_booking_log_tool(
                    booking_code=arguments["booking_code"],
                    customer_name=arguments["customer_name"],
                    customer_id=arguments.get("customer_id"),
                    date_iso=arguments.get("date_iso"),
                    time_iso=arguments.get("time_iso"),
                    area_id=arguments.get("area_id"),
                    area_name=arguments.get("area_name"),
                    specialty_id=arguments.get("specialty_id"),
                    specialty_name=arguments.get("specialty_name"),
                    professional_id=arguments.get("professional_id"),
                    professional_name=arguments.get("professional_name"),
                    observations=arguments.get("observations"),
                )
            elif tool_name == "get_booking_log":
                result = get_booking_log_tool(
                    booking_code=arguments.get("booking_code"),
                    log_id=arguments.get("log_id"),
                )
            elif tool_name == "list_booking_logs":
                result = list_booking_logs_tool(
                    customer_id=arguments.get("customer_id"),
                    customer_name=arguments.get("customer_name"),
                    date_iso=arguments.get("date_iso"),
                    professional_id=arguments.get("professional_id"),
                    specialty_id=arguments.get("specialty_id"),
                    area_id=arguments.get("area_id"),
                    limit=arguments.get("limit", 100),
                )
            elif tool_name == "update_booking_log":
                result = update_booking_log_tool(
                    booking_code=arguments.get("booking_code"),
                    log_id=arguments.get("log_id"),
                    customer_name=arguments.get("customer_name"),
                    date_iso=arguments.get("date_iso"),
                    time_iso=arguments.get("time_iso"),
                    area_id=arguments.get("area_id"),
                    area_name=arguments.get("area_name"),
                    specialty_id=arguments.get("specialty_id"),
                    specialty_name=arguments.get("specialty_name"),
                    professional_id=arguments.get("professional_id"),
                    professional_name=arguments.get("professional_name"),
                    observations=arguments.get("observations"),
                )
            elif tool_name == "delete_booking_log":
                result = delete_booking_log_tool(
                    booking_code=arguments.get("booking_code"),
                    log_id=arguments.get("log_id"),
                )
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
    return {"status": "ok", "service": "mcp-booking-log-server"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("BOOKING_LOG_SERVER_PORT", "60003"))
    uvicorn.run(app, host="0.0.0.0", port=port)

