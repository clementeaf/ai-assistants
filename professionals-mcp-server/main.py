#!/usr/bin/env python3
"""MCP Professionals Server - Management of professionals, areas, and specialties."""

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

app = FastAPI(title="MCP Professionals Server", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = Path(os.getenv("PROFESSIONALS_DB_PATH", "professionals.db"))


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
        # Áreas
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS areas (
                area_id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TEXT NOT NULL
            )
            """
        )

        # Especialidades
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS specialties (
                specialty_id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                area_id TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (area_id) REFERENCES areas(area_id)
            )
            """
        )

        # Profesionales
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS professionals (
                professional_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
            """
        )

        # Relación Profesional-Especialidad (muchos a muchos)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS professional_specialties (
                professional_id TEXT NOT NULL,
                specialty_id TEXT NOT NULL,
                PRIMARY KEY (professional_id, specialty_id),
                FOREIGN KEY (professional_id) REFERENCES professionals(professional_id),
                FOREIGN KEY (specialty_id) REFERENCES specialties(specialty_id)
            )
            """
        )

        # Índices
        conn.execute("CREATE INDEX IF NOT EXISTS idx_specialties_area ON specialties(area_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_professional_specialties_prof ON professional_specialties(professional_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_professional_specialties_spec ON professional_specialties(specialty_id)")


def create_area_tool(name: str, description: str | None = None) -> dict:
    """Create a new area."""
    area_id = f"AREA-{uuid.uuid4().hex[:8].upper()}"
    created_at = datetime.now(tz=timezone.utc).isoformat()

    with get_db() as conn:
        conn.execute(
            "INSERT INTO areas (area_id, name, description, created_at) VALUES (?, ?, ?, ?)",
            (area_id, name, description or "", created_at),
        )

    return {
        "area": {
            "area_id": area_id,
            "name": name,
            "description": description,
            "created_at": created_at,
        }
    }


def get_area_tool(area_id: str) -> dict:
    """Get an area by ID."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM areas WHERE area_id = ?", (area_id,))
        row = cursor.fetchone()
        if row is None:
            return {"area": None}

        return {
            "area": {
                "area_id": row["area_id"],
                "name": row["name"],
                "description": row["description"],
                "created_at": row["created_at"],
            }
        }


def list_areas_tool() -> dict:
    """List all areas."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM areas ORDER BY name")
        rows = cursor.fetchall()

    areas = [
        {
            "area_id": row["area_id"],
            "name": row["name"],
            "description": row["description"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]

    return {"areas": areas}


def create_specialty_tool(name: str, area_id: str | None = None, description: str | None = None) -> dict:
    """Create a new specialty."""
    specialty_id = f"SPEC-{uuid.uuid4().hex[:8].upper()}"
    created_at = datetime.now(tz=timezone.utc).isoformat()

    with get_db() as conn:
        conn.execute(
            "INSERT INTO specialties (specialty_id, name, description, area_id, created_at) VALUES (?, ?, ?, ?, ?)",
            (specialty_id, name, description or "", area_id, created_at),
        )

    return {
        "specialty": {
            "specialty_id": specialty_id,
            "name": name,
            "description": description,
            "area_id": area_id,
            "created_at": created_at,
        }
    }


def get_specialty_tool(specialty_id: str) -> dict:
    """Get a specialty by ID."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM specialties WHERE specialty_id = ?", (specialty_id,))
        row = cursor.fetchone()
        if row is None:
            return {"specialty": None}

        return {
            "specialty": {
                "specialty_id": row["specialty_id"],
                "name": row["name"],
                "description": row["description"],
                "area_id": row["area_id"],
                "created_at": row["created_at"],
            }
        }


def list_specialties_tool(area_id: str | None = None) -> dict:
    """List specialties, optionally filtered by area."""
    with get_db() as conn:
        if area_id:
            cursor = conn.execute("SELECT * FROM specialties WHERE area_id = ? ORDER BY name", (area_id,))
        else:
            cursor = conn.execute("SELECT * FROM specialties ORDER BY name")
        rows = cursor.fetchall()

    specialties = [
        {
            "specialty_id": row["specialty_id"],
            "name": row["name"],
            "description": row["description"],
            "area_id": row["area_id"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]

    return {"specialties": specialties}


def create_professional_tool(name: str, email: str | None = None, phone: str | None = None) -> dict:
    """Create a new professional."""
    professional_id = f"PROF-{uuid.uuid4().hex[:8].upper()}"
    created_at = datetime.now(tz=timezone.utc).isoformat()

    with get_db() as conn:
        conn.execute(
            "INSERT INTO professionals (professional_id, name, email, phone, active, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (professional_id, name, email or "", phone or "", 1, created_at),
        )

    return {
        "professional": {
            "professional_id": professional_id,
            "name": name,
            "email": email,
            "phone": phone,
            "active": True,
            "created_at": created_at,
        }
    }


def get_professional_tool(professional_id: str) -> dict:
    """Get a professional by ID."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM professionals WHERE professional_id = ?", (professional_id,))
        row = cursor.fetchone()
        if row is None:
            return {"professional": None}

        # Obtener especialidades del profesional
        cursor_specs = conn.execute(
            """
            SELECT s.specialty_id, s.name, s.description, s.area_id
            FROM specialties s
            JOIN professional_specialties ps ON s.specialty_id = ps.specialty_id
            WHERE ps.professional_id = ?
            """,
            (professional_id,),
        )
        specialties = [
            {
                "specialty_id": spec["specialty_id"],
                "name": spec["name"],
                "description": spec["description"],
                "area_id": spec["area_id"],
            }
            for spec in cursor_specs.fetchall()
        ]

        return {
            "professional": {
                "professional_id": row["professional_id"],
                "name": row["name"],
                "email": row["email"],
                "phone": row["phone"],
                "active": bool(row["active"]),
                "created_at": row["created_at"],
                "specialties": specialties,
            }
        }


def list_professionals_tool(specialty_id: str | None = None, area_id: str | None = None) -> dict:
    """List professionals, optionally filtered by specialty or area."""
    with get_db() as conn:
        if specialty_id:
            cursor = conn.execute(
                """
                SELECT DISTINCT p.* FROM professionals p
                JOIN professional_specialties ps ON p.professional_id = ps.professional_id
                WHERE ps.specialty_id = ? AND p.active = 1
                ORDER BY p.name
                """,
                (specialty_id,),
            )
        elif area_id:
            cursor = conn.execute(
                """
                SELECT DISTINCT p.* FROM professionals p
                JOIN professional_specialties ps ON p.professional_id = ps.professional_id
                JOIN specialties s ON ps.specialty_id = s.specialty_id
                WHERE s.area_id = ? AND p.active = 1
                ORDER BY p.name
                """,
                (area_id,),
            )
        else:
            cursor = conn.execute("SELECT * FROM professionals WHERE active = 1 ORDER BY name")
        rows = cursor.fetchall()

    professionals = [
        {
            "professional_id": row["professional_id"],
            "name": row["name"],
            "email": row["email"],
            "phone": row["phone"],
            "active": bool(row["active"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]

    return {"professionals": professionals}


def assign_specialty_tool(professional_id: str, specialty_id: str) -> dict:
    """Assign a specialty to a professional."""
    with get_db() as conn:
        try:
            conn.execute(
                "INSERT INTO professional_specialties (professional_id, specialty_id) VALUES (?, ?)",
                (professional_id, specialty_id),
            )
            return {"success": True}
        except sqlite3.IntegrityError:
            return {"success": False, "error": "Already assigned"}


def remove_specialty_tool(professional_id: str, specialty_id: str) -> dict:
    """Remove a specialty from a professional."""
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM professional_specialties WHERE professional_id = ? AND specialty_id = ?",
            (professional_id, specialty_id),
        )
        return {"success": cursor.rowcount > 0}


def update_professional_tool(
    professional_id: str,
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    active: bool | None = None,
) -> dict:
    """Update a professional."""
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM professionals WHERE professional_id = ?", (professional_id,))
        row = cursor.fetchone()
        if row is None:
            return {"professional": None}

        updates = []
        params = []
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if email is not None:
            updates.append("email = ?")
            params.append(email)
        if phone is not None:
            updates.append("phone = ?")
            params.append(phone)
        if active is not None:
            updates.append("active = ?")
            params.append(1 if active else 0)

        if updates:
            params.append(professional_id)
            conn.execute(f"UPDATE professionals SET {', '.join(updates)} WHERE professional_id = ?", params)

        cursor = conn.execute("SELECT * FROM professionals WHERE professional_id = ?", (professional_id,))
        row = cursor.fetchone()

        # Obtener especialidades
        cursor_specs = conn.execute(
            """
            SELECT s.specialty_id, s.name, s.description, s.area_id
            FROM specialties s
            JOIN professional_specialties ps ON s.specialty_id = ps.specialty_id
            WHERE ps.professional_id = ?
            """,
            (professional_id,),
        )
        specialties = [
            {
                "specialty_id": spec["specialty_id"],
                "name": spec["name"],
                "description": spec["description"],
                "area_id": spec["area_id"],
            }
            for spec in cursor_specs.fetchall()
        ]

        return {
            "professional": {
                "professional_id": row["professional_id"],
                "name": row["name"],
                "email": row["email"],
                "phone": row["phone"],
                "active": bool(row["active"]),
                "created_at": row["created_at"],
                "specialties": specialties,
            }
        }


def delete_professional_tool(professional_id: str) -> dict:
    """Delete (deactivate) a professional."""
    with get_db() as conn:
        cursor = conn.execute("UPDATE professionals SET active = 0 WHERE professional_id = ?", (professional_id,))
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

            # Áreas
            if tool_name == "create_area":
                result = create_area_tool(
                    name=arguments["name"],
                    description=arguments.get("description"),
                )
            elif tool_name == "get_area":
                result = get_area_tool(area_id=arguments["area_id"])
            elif tool_name == "list_areas":
                result = list_areas_tool()

            # Especialidades
            elif tool_name == "create_specialty":
                result = create_specialty_tool(
                    name=arguments["name"],
                    area_id=arguments.get("area_id"),
                    description=arguments.get("description"),
                )
            elif tool_name == "get_specialty":
                result = get_specialty_tool(specialty_id=arguments["specialty_id"])
            elif tool_name == "list_specialties":
                result = list_specialties_tool(area_id=arguments.get("area_id"))

            # Profesionales
            elif tool_name == "create_professional":
                result = create_professional_tool(
                    name=arguments["name"],
                    email=arguments.get("email"),
                    phone=arguments.get("phone"),
                )
            elif tool_name == "get_professional":
                result = get_professional_tool(professional_id=arguments["professional_id"])
            elif tool_name == "list_professionals":
                result = list_professionals_tool(
                    specialty_id=arguments.get("specialty_id"),
                    area_id=arguments.get("area_id"),
                )
            elif tool_name == "assign_specialty":
                result = assign_specialty_tool(
                    professional_id=arguments["professional_id"],
                    specialty_id=arguments["specialty_id"],
                )
            elif tool_name == "remove_specialty":
                result = remove_specialty_tool(
                    professional_id=arguments["professional_id"],
                    specialty_id=arguments["specialty_id"],
                )
            elif tool_name == "update_professional":
                result = update_professional_tool(
                    professional_id=arguments["professional_id"],
                    name=arguments.get("name"),
                    email=arguments.get("email"),
                    phone=arguments.get("phone"),
                    active=arguments.get("active"),
                )
            elif tool_name == "delete_professional":
                result = delete_professional_tool(professional_id=arguments["professional_id"])
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
    return {"status": "ok", "service": "mcp-professionals-server"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PROFESSIONALS_SERVER_PORT", "3002"))
    uvicorn.run(app, host="0.0.0.0", port=port)

