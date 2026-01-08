#!/usr/bin/env python3
"""MCP Booking Flow Server - Conversation flow configuration for booking bot."""

from __future__ import annotations

import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

DB_PATH = Path(os.getenv("BOOKING_FLOW_DB_PATH", "booking_flow.db"))


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
        # Flow definitions
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS flows (
                flow_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                domain TEXT NOT NULL DEFAULT 'bookings',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        # Flow stages/steps
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS flow_stages (
                stage_id TEXT PRIMARY KEY,
                flow_id TEXT NOT NULL,
                stage_order INTEGER NOT NULL,
                stage_name TEXT NOT NULL,
                stage_type TEXT NOT NULL,
                prompt_text TEXT,
                field_name TEXT,
                field_type TEXT,
                validation_rules TEXT,
                is_required INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (flow_id) REFERENCES flows(flow_id) ON DELETE CASCADE
            )
            """
        )

        # Indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_flows_domain ON flows(domain)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_flows_active ON flows(is_active)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_stages_flow ON flow_stages(flow_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_stages_order ON flow_stages(flow_id, stage_order)")

        # Create default booking flow if it doesn't exist
        cursor = conn.execute("SELECT COUNT(*) FROM flows WHERE domain = 'bookings'")
        if cursor.fetchone()[0] == 0:
            create_default_booking_flow(conn)


def create_default_booking_flow(conn: sqlite3.Connection) -> None:
    """Create default booking flow with common stages."""
    flow_id = f"FLOW-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(tz=timezone.utc).isoformat()

    conn.execute(
        """
        INSERT INTO flows (flow_id, name, description, domain, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (flow_id, "Default Booking Flow", "Flujo predeterminado para reservas", "bookings", 1, now, now),
    )

    default_stages = [
        (1, "greeting", "greeting", "Hola, soy tu asistente de reservas. ¿Cómo te llamas?", None, None, None, 0),
        (2, "get_name", "input", "Por favor, dime tu nombre completo.", "customer_name", "text", None, 1),
        (3, "get_date", "input", "¿Para qué fecha te gustaría hacer la reserva?", "booking_date", "date", None, 1),
        (4, "get_time", "input", "¿A qué hora prefieres? (formato: HH:MM)", "booking_time", "time", None, 1),
        (5, "get_service", "input", "¿Qué tipo de servicio necesitas?", "service_type", "text", None, 0),
        (6, "confirm", "confirmation", "¿Confirmas la reserva para {booking_date} a las {booking_time}?", None, None, None, 1),
    ]

    for order, name, stage_type, prompt, field_name, field_type, validation, is_required in default_stages:
        stage_id = f"STAGE-{uuid.uuid4().hex[:8].upper()}"
        conn.execute(
            """
            INSERT INTO flow_stages (
                stage_id, flow_id, stage_order, stage_name, stage_type,
                prompt_text, field_name, field_type, validation_rules, is_required, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (stage_id, flow_id, order, name, stage_type, prompt, field_name, field_type, validation, is_required, now, now),
        )


def create_flow_tool(
    name: str,
    description: str | None = None,
    domain: str = "bookings",
) -> dict:
    """Create a new conversation flow."""
    flow_id = f"FLOW-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(tz=timezone.utc).isoformat()

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO flows (flow_id, name, description, domain, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (flow_id, name, description or "", domain, 1, now, now),
        )

    return {
        "flow": {
            "flow_id": flow_id,
            "name": name,
            "description": description,
            "domain": domain,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    }


def get_flow_tool(flow_id: str | None = None, domain: str | None = None) -> dict:
    """Get a flow by ID or get active flow for domain."""
    with get_db() as conn:
        if flow_id:
            cursor = conn.execute("SELECT * FROM flows WHERE flow_id = ?", (flow_id,))
        elif domain:
            cursor = conn.execute("SELECT * FROM flows WHERE domain = ? AND is_active = 1 ORDER BY created_at DESC LIMIT 1", (domain,))
        else:
            return {"flow": None}

        row = cursor.fetchone()
        if row is None:
            return {"flow": None}

        return {
            "flow": {
                "flow_id": row["flow_id"],
                "name": row["name"],
                "description": row["description"],
                "domain": row["domain"],
                "is_active": bool(row["is_active"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        }


def list_flows_tool(domain: str | None = None, include_inactive: bool = False) -> dict:
    """List all flows, optionally filtered by domain."""
    with get_db() as conn:
        if domain:
            if include_inactive:
                cursor = conn.execute("SELECT * FROM flows WHERE domain = ? ORDER BY created_at DESC", (domain,))
            else:
                cursor = conn.execute("SELECT * FROM flows WHERE domain = ? AND is_active = 1 ORDER BY created_at DESC", (domain,))
        else:
            if include_inactive:
                cursor = conn.execute("SELECT * FROM flows ORDER BY created_at DESC")
            else:
                cursor = conn.execute("SELECT * FROM flows WHERE is_active = 1 ORDER BY created_at DESC")

        rows = cursor.fetchall()

    flows = [
        {
            "flow_id": row["flow_id"],
            "name": row["name"],
            "description": row["description"],
            "domain": row["domain"],
            "is_active": bool(row["is_active"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        for row in rows
    ]

    return {"flows": flows, "count": len(flows)}


def add_stage_tool(
    flow_id: str,
    stage_order: int,
    stage_name: str,
    stage_type: str,
    prompt_text: str | None = None,
    field_name: str | None = None,
    field_type: str | None = None,
    validation_rules: str | None = None,
    is_required: bool = True,
) -> dict:
    """Add a stage to a flow."""
    stage_id = f"STAGE-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(tz=timezone.utc).isoformat()

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO flow_stages (
                stage_id, flow_id, stage_order, stage_name, stage_type,
                prompt_text, field_name, field_type, validation_rules, is_required, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                stage_id,
                flow_id,
                stage_order,
                stage_name,
                stage_type,
                prompt_text or "",
                field_name,
                field_type,
                validation_rules,
                1 if is_required else 0,
                now,
                now,
            ),
        )

    return {
        "stage": {
            "stage_id": stage_id,
            "flow_id": flow_id,
            "stage_order": stage_order,
            "stage_name": stage_name,
            "stage_type": stage_type,
            "prompt_text": prompt_text,
            "field_name": field_name,
            "field_type": field_type,
            "validation_rules": validation_rules,
            "is_required": is_required,
            "created_at": now,
            "updated_at": now,
        }
    }


def get_flow_stages_tool(flow_id: str) -> dict:
    """Get all stages for a flow, ordered by stage_order."""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM flow_stages WHERE flow_id = ? ORDER BY stage_order ASC",
            (flow_id,),
        )
        rows = cursor.fetchall()

    stages = [
        {
            "stage_id": row["stage_id"],
            "flow_id": row["flow_id"],
            "stage_order": row["stage_order"],
            "stage_name": row["stage_name"],
            "stage_type": row["stage_type"],
            "prompt_text": row["prompt_text"],
            "field_name": row["field_name"],
            "field_type": row["field_type"],
            "validation_rules": row["validation_rules"],
            "is_required": bool(row["is_required"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        for row in rows
    ]

    return {"stages": stages, "count": len(stages)}


def update_stage_tool(
    stage_id: str,
    stage_order: int | None = None,
    stage_name: str | None = None,
    prompt_text: str | None = None,
    field_name: str | None = None,
    field_type: str | None = None,
    validation_rules: str | None = None,
    is_required: bool | None = None,
) -> dict:
    """Update a flow stage."""
    with get_db() as conn:
        updates = []
        params = []
        if stage_order is not None:
            updates.append("stage_order = ?")
            params.append(stage_order)
        if stage_name is not None:
            updates.append("stage_name = ?")
            params.append(stage_name)
        if prompt_text is not None:
            updates.append("prompt_text = ?")
            params.append(prompt_text)
        if field_name is not None:
            updates.append("field_name = ?")
            params.append(field_name)
        if field_type is not None:
            updates.append("field_type = ?")
            params.append(field_type)
        if validation_rules is not None:
            updates.append("validation_rules = ?")
            params.append(validation_rules)
        if is_required is not None:
            updates.append("is_required = ?")
            params.append(1 if is_required else 0)

        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.now(tz=timezone.utc).isoformat())
            params.append(stage_id)
            conn.execute(f"UPDATE flow_stages SET {', '.join(updates)} WHERE stage_id = ?", params)

        cursor = conn.execute("SELECT * FROM flow_stages WHERE stage_id = ?", (stage_id,))
        row = cursor.fetchone()
        if row is None:
            return {"stage": None}

        return {
            "stage": {
                "stage_id": row["stage_id"],
                "flow_id": row["flow_id"],
                "stage_order": row["stage_order"],
                "stage_name": row["stage_name"],
                "stage_type": row["stage_type"],
                "prompt_text": row["prompt_text"],
                "field_name": row["field_name"],
                "field_type": row["field_type"],
                "validation_rules": row["validation_rules"],
                "is_required": bool(row["is_required"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        }


def delete_stage_tool(stage_id: str) -> dict:
    """Delete a flow stage."""
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM flow_stages WHERE stage_id = ?", (stage_id,))
        return {"success": cursor.rowcount > 0}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    init_db()
    yield


app = FastAPI(title="MCP Booking Flow Server", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/mcp")
async def mcp_endpoint(request: MCPRequest):
    """Handle MCP JSON-RPC requests."""
    method = request.method
    params = request.params or {}

    try:
        if method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name == "create_flow":
                result = create_flow_tool(
                    name=arguments["name"],
                    description=arguments.get("description"),
                    domain=arguments.get("domain", "bookings"),
                )
            elif tool_name == "get_flow":
                result = get_flow_tool(
                    flow_id=arguments.get("flow_id"),
                    domain=arguments.get("domain"),
                )
            elif tool_name == "list_flows":
                result = list_flows_tool(
                    domain=arguments.get("domain"),
                    include_inactive=arguments.get("include_inactive", False),
                )
            elif tool_name == "add_stage":
                result = add_stage_tool(
                    flow_id=arguments["flow_id"],
                    stage_order=arguments["stage_order"],
                    stage_name=arguments["stage_name"],
                    stage_type=arguments["stage_type"],
                    prompt_text=arguments.get("prompt_text"),
                    field_name=arguments.get("field_name"),
                    field_type=arguments.get("field_type"),
                    validation_rules=arguments.get("validation_rules"),
                    is_required=arguments.get("is_required", True),
                )
            elif tool_name == "get_flow_stages":
                result = get_flow_stages_tool(flow_id=arguments["flow_id"])
            elif tool_name == "update_stage":
                result = update_stage_tool(
                    stage_id=arguments["stage_id"],
                    stage_order=arguments.get("stage_order"),
                    stage_name=arguments.get("stage_name"),
                    prompt_text=arguments.get("prompt_text"),
                    field_name=arguments.get("field_name"),
                    field_type=arguments.get("field_type"),
                    validation_rules=arguments.get("validation_rules"),
                    is_required=arguments.get("is_required"),
                )
            elif tool_name == "delete_stage":
                result = delete_stage_tool(stage_id=arguments["stage_id"])
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
    return {"status": "ok", "service": "mcp-booking-flow-server"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("BOOKING_FLOW_SERVER_PORT", "3006"))
    uvicorn.run(app, host="0.0.0.0", port=port)

