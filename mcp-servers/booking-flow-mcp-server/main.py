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

# Importar funciones de gestión de autómatas
try:
    from automata_management import (
        create_automaton,
        create_automaton_version,
        add_automaton_tool,
        create_automaton_test,
        record_test_result,
        record_automaton_metric,
        get_automaton_full_info,
    )
except ImportError:
    # Si el módulo no está disponible, las funciones se definen inline más abajo
    pass

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

        # Tabla principal de autómatas (expandida)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS automata (
                automaton_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                domain TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                created_by TEXT,
                tags TEXT,
                metadata_json TEXT
            )
            """
        )

        # Versiones de prompts del autómata (versionado)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS automata_versions (
                version_id TEXT PRIMARY KEY,
                automaton_id TEXT NOT NULL,
                version_number INTEGER NOT NULL,
                system_prompt TEXT NOT NULL,
                prompt_hash TEXT,
                change_description TEXT,
                created_at TEXT NOT NULL,
                created_by TEXT,
                is_current INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (automaton_id) REFERENCES automata(automaton_id) ON DELETE CASCADE,
                UNIQUE(automaton_id, version_number)
            )
            """
        )

        # Herramientas/funciones usadas por cada autómata
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS automata_tools (
                tool_id TEXT PRIMARY KEY,
                automaton_id TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                tool_description TEXT,
                tool_input_schema TEXT,
                tool_output_schema TEXT,
                is_required INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY (automaton_id) REFERENCES automata(automaton_id) ON DELETE CASCADE,
                UNIQUE(automaton_id, tool_name)
            )
            """
        )

        # Tests definidos para autómatas
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS automata_tests (
                test_id TEXT PRIMARY KEY,
                automaton_id TEXT NOT NULL,
                test_name TEXT NOT NULL,
                test_description TEXT,
                test_type TEXT NOT NULL,
                test_scenario TEXT NOT NULL,
                expected_result TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                created_by TEXT,
                FOREIGN KEY (automaton_id) REFERENCES automata(automaton_id) ON DELETE CASCADE
            )
            """
        )

        # Resultados de ejecución de tests
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS automata_test_results (
                result_id TEXT PRIMARY KEY,
                test_id TEXT NOT NULL,
                automaton_id TEXT NOT NULL,
                version_id TEXT,
                execution_status TEXT NOT NULL,
                actual_result TEXT,
                execution_time_ms INTEGER,
                error_message TEXT,
                error_stack TEXT,
                executed_at TEXT NOT NULL,
                executed_by TEXT,
                metadata_json TEXT,
                FOREIGN KEY (test_id) REFERENCES automata_tests(test_id) ON DELETE CASCADE,
                FOREIGN KEY (automaton_id) REFERENCES automata(automaton_id) ON DELETE CASCADE,
                FOREIGN KEY (version_id) REFERENCES automata_versions(version_id) ON DELETE SET NULL
            )
            """
        )

        # Historial de cambios en autómatas
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS automata_changes (
                change_id TEXT PRIMARY KEY,
                automaton_id TEXT NOT NULL,
                change_type TEXT NOT NULL,
                change_description TEXT NOT NULL,
                before_state TEXT,
                after_state TEXT,
                changed_by TEXT,
                changed_at TEXT NOT NULL,
                FOREIGN KEY (automaton_id) REFERENCES automata(automaton_id) ON DELETE CASCADE
            )
            """
        )

        # Métricas de rendimiento y evaluación
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS automata_metrics (
                metric_id TEXT PRIMARY KEY,
                automaton_id TEXT NOT NULL,
                version_id TEXT,
                metric_type TEXT NOT NULL,
                metric_value REAL NOT NULL,
                metric_unit TEXT,
                evaluation_date TEXT NOT NULL,
                sample_size INTEGER,
                metadata_json TEXT,
                FOREIGN KEY (automaton_id) REFERENCES automata(automaton_id) ON DELETE CASCADE,
                FOREIGN KEY (version_id) REFERENCES automata_versions(version_id) ON DELETE SET NULL
            )
            """
        )

        # Índices para optimización
        conn.execute("CREATE INDEX IF NOT EXISTS idx_automata_domain ON automata(domain)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_automata_active ON automata(is_active)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_automata_versions_automaton ON automata_versions(automaton_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_automata_versions_current ON automata_versions(automaton_id, is_current)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_automata_tools_automaton ON automata_tools(automaton_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_automata_tests_automaton ON automata_tests(automaton_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_automata_tests_active ON automata_tests(automaton_id, is_active)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_test_results_test ON automata_test_results(test_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_test_results_automaton ON automata_test_results(automaton_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_test_results_status ON automata_test_results(execution_status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_test_results_executed ON automata_test_results(executed_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_changes_automaton ON automata_changes(automaton_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_changes_date ON automata_changes(changed_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_automaton ON automata_metrics(automaton_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_type ON automata_metrics(metric_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_date ON automata_metrics(evaluation_date)")

        # Create default booking flow if it doesn't exist
        cursor = conn.execute("SELECT COUNT(*) FROM flows WHERE domain = 'bookings'")
        if cursor.fetchone()[0] == 0:
            create_default_booking_flow(conn)
        
        # Agregar stage system_prompt a flujos de bookings existentes que no lo tengan
        ensure_system_prompt_stage(conn)
        
        # Migrar flows existentes a automata si no existen
        _migrate_flows_to_automata_inline(conn)


def _migrate_flows_to_automata_inline(conn: sqlite3.Connection) -> None:
    """Migra flows existentes a la tabla automata si no existen (versión inline)."""
    import hashlib
    import json
    
    cursor = conn.execute(
        """
        SELECT f.flow_id, f.name, f.description, f.domain, f.is_active, f.created_at, f.updated_at
        FROM flows f
        LEFT JOIN automata a ON f.flow_id = a.automaton_id
        WHERE a.automaton_id IS NULL
        """
    )
    flows_to_migrate = cursor.fetchall()
    
    for flow in flows_to_migrate:
        automaton_id = flow["flow_id"]
        now = datetime.now(tz=timezone.utc).isoformat()
        
        # Crear entrada en automata
        conn.execute(
            """
            INSERT INTO automata (
                automaton_id, name, description, domain, version, is_active,
                created_at, updated_at, created_by, tags, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                automaton_id,
                flow["name"],
                flow["description"],
                flow["domain"],
                1,
                flow["is_active"],
                flow["created_at"],
                flow["updated_at"],
                "system",
                json.dumps([]),
                json.dumps({"migrated_from_flow": True}),
            ),
        )
        
        # Obtener el system_prompt del flow
        cursor = conn.execute(
            """
            SELECT prompt_text FROM flow_stages
            WHERE flow_id = ? AND stage_type = 'system_prompt'
            LIMIT 1
            """
        )
        prompt_row = cursor.fetchone()
        system_prompt = prompt_row["prompt_text"] if prompt_row else ""
        
        if system_prompt:
            # Crear versión inicial
            version_id = f"VERSION-{uuid.uuid4().hex[:8].upper()}"
            prompt_hash = hashlib.sha256(system_prompt.encode()).hexdigest()[:16]
            
            conn.execute(
                """
                INSERT INTO automata_versions (
                    version_id, automaton_id, version_number, system_prompt,
                    prompt_hash, change_description, created_at, created_by, is_current
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version_id,
                    automaton_id,
                    1,
                    system_prompt,
                    prompt_hash,
                    "Versión inicial migrada desde flow",
                    now,
                    "system",
                    1,
                ),
            )
        
        # Registrar cambio
        conn.execute(
            """
            INSERT INTO automata_changes (
                change_id, automaton_id, change_type, change_description,
                before_state, after_state, changed_by, changed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"CHANGE-{uuid.uuid4().hex[:8].upper()}",
                automaton_id,
                "creation",
                "Autómata creado desde migración de flow",
                None,
                json.dumps({"flow_id": automaton_id, "name": flow["name"]}),
                "system",
                now,
            ),
        )


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
    
    # Agregar stage system_prompt con el prompt del LLM
    system_prompt_text = _load_system_prompt()
    if system_prompt_text:
        stage_id = f"STAGE-{uuid.uuid4().hex[:8].upper()}"
        max_order = max([s[0] for s in default_stages]) if default_stages else 0
        conn.execute(
            """
            INSERT INTO flow_stages (
                stage_id, flow_id, stage_order, stage_name, stage_type,
                prompt_text, field_name, field_type, validation_rules, is_required, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (stage_id, flow_id, max_order + 1, "system_prompt", "system_prompt", system_prompt_text, None, None, None, 0, now, now),
        )


def _load_system_prompt() -> str | None:
    """Carga el prompt del sistema desde autonomous_system.txt."""
    try:
        # Intentar cargar desde la ruta relativa al backend
        import sys
        from pathlib import Path
        
        # Buscar el archivo en diferentes ubicaciones posibles
        possible_paths = [
            Path(__file__).resolve().parents[2] / "apps" / "backend" / "prompts" / "autonomous_system.txt",
            Path(__file__).resolve().parents[1] / ".." / "apps" / "backend" / "prompts" / "autonomous_system.txt",
            Path.cwd() / "apps" / "backend" / "prompts" / "autonomous_system.txt",
        ]
        
        for path in possible_paths:
            if path.exists():
                return path.read_text(encoding="utf-8")
        
        # Si no se encuentra, retornar un prompt por defecto
        return None
    except Exception:
        return None


def ensure_system_prompt_stage(conn: sqlite3.Connection) -> None:
    """Asegura que todos los flujos de bookings tengan un stage system_prompt."""
    # Obtener todos los flujos de bookings activos
    cursor = conn.execute("SELECT flow_id FROM flows WHERE domain = 'bookings' AND is_active = 1")
    flows = cursor.fetchall()
    
    system_prompt_text = _load_system_prompt()
    if not system_prompt_text:
        return  # No podemos agregar el stage sin el prompt
    
    now = datetime.now(tz=timezone.utc).isoformat()
    
    for flow_row in flows:
        flow_id = flow_row["flow_id"]
        
        # Verificar si ya tiene un stage system_prompt
        cursor = conn.execute(
            "SELECT COUNT(*) FROM flow_stages WHERE flow_id = ? AND stage_type = 'system_prompt'",
            (flow_id,)
        )
        if cursor.fetchone()[0] > 0:
            continue  # Ya tiene system_prompt
        
        # Obtener el máximo stage_order para agregar al final
        cursor = conn.execute(
            "SELECT MAX(stage_order) as max_order FROM flow_stages WHERE flow_id = ?",
            (flow_id,)
        )
        row = cursor.fetchone()
        next_order = (row["max_order"] or 0) + 1
        
        # Agregar el stage system_prompt
        stage_id = f"STAGE-{uuid.uuid4().hex[:8].upper()}"
        conn.execute(
            """
            INSERT INTO flow_stages (
                stage_id, flow_id, stage_order, stage_name, stage_type,
                prompt_text, field_name, field_type, validation_rules, is_required, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (stage_id, flow_id, next_order, "system_prompt", "system_prompt", system_prompt_text, None, None, None, 0, now, now),
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


def delete_flow_tool(flow_id: str) -> dict:
    """Delete a flow and all its stages."""
    with get_db() as conn:
        # Primero eliminar todas las etapas del flujo
        conn.execute("DELETE FROM flow_stages WHERE flow_id = ?", (flow_id,))
        # Luego eliminar el flujo
        cursor = conn.execute("DELETE FROM flows WHERE flow_id = ?", (flow_id,))
        return {"success": cursor.rowcount > 0}


# ============================================================================
# Funciones para gestión completa de autómatas
# ============================================================================

def get_automaton_tool(automaton_id: str) -> dict:
    """Obtiene información completa de un autómata."""
    import json
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM automata WHERE automaton_id = ?", (automaton_id,))
        automaton = cursor.fetchone()
        if not automaton:
            return {"automaton": None}
        
        result = dict(automaton)
        result["tags"] = json.loads(automaton["tags"] or "[]")
        result["metadata"] = json.loads(automaton["metadata_json"] or "{}")
        
        # Versión actual
        cursor = conn.execute(
            """
            SELECT * FROM automata_versions
            WHERE automaton_id = ? AND is_current = 1
            LIMIT 1
            """
        )
        current_version = cursor.fetchone()
        if current_version:
            result["current_version"] = dict(current_version)
        
        # Herramientas
        cursor = conn.execute(
            "SELECT * FROM automata_tools WHERE automaton_id = ? ORDER BY tool_name",
            (automaton_id,)
        )
        tools = []
        for row in cursor.fetchall():
            tool = dict(row)
            tool["input_schema"] = json.loads(tool["tool_input_schema"] or "{}")
            tool["output_schema"] = json.loads(tool["tool_output_schema"] or "{}")
            tools.append(tool)
        result["tools"] = tools
        
        # Tests activos
        cursor = conn.execute(
            "SELECT * FROM automata_tests WHERE automaton_id = ? AND is_active = 1 ORDER BY created_at DESC",
            (automaton_id,)
        )
        tests = []
        for row in cursor.fetchall():
            test = dict(row)
            test["scenario"] = json.loads(test["test_scenario"])
            test["expected_result"] = json.loads(test["expected_result"]) if test["expected_result"] else None
            tests.append(test)
        result["tests"] = tests
        
        return {"automaton": result}


def list_automata_tool(domain: str | None = None, include_inactive: bool = False) -> dict:
    """Lista todos los autómatas."""
    import json
    with get_db() as conn:
        query = "SELECT * FROM automata WHERE 1=1"
        params = []
        
        if domain:
            query += " AND domain = ?"
            params.append(domain)
        
        if not include_inactive:
            query += " AND is_active = 1"
        
        query += " ORDER BY created_at DESC"
        
        cursor = conn.execute(query, params)
        automata = []
        for row in cursor.fetchall():
            automaton = dict(row)
            automaton["tags"] = json.loads(automaton["tags"] or "[]")
            automaton["metadata"] = json.loads(automaton["metadata_json"] or "{}")
            automata.append(automaton)
        
        return {"automata": automata, "count": len(automata)}


def create_automaton_version_tool(
    automaton_id: str,
    system_prompt: str,
    change_description: str,
    created_by: str | None = None,
) -> dict:
    """Crea una nueva versión del prompt del autómata."""
    import hashlib
    import json
    with get_db() as conn:
        now = datetime.now(tz=timezone.utc).isoformat()
        created_by = created_by or "system"
        
        # Obtener versión actual
        cursor = conn.execute(
            "SELECT MAX(version_number) as max_version FROM automata_versions WHERE automaton_id = ?",
            (automaton_id,)
        )
        row = cursor.fetchone()
        next_version = (row["max_version"] or 0) + 1
        
        # Desactivar versión actual
        conn.execute(
            "UPDATE automata_versions SET is_current = 0 WHERE automaton_id = ? AND is_current = 1",
            (automaton_id,)
        )
        
        # Crear nueva versión
        version_id = f"VERSION-{uuid.uuid4().hex[:8].upper()}"
        prompt_hash = hashlib.sha256(system_prompt.encode()).hexdigest()[:16]
        
        conn.execute(
            """
            INSERT INTO automata_versions (
                version_id, automaton_id, version_number, system_prompt,
                prompt_hash, change_description, created_at, created_by, is_current
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                version_id,
                automaton_id,
                next_version,
                system_prompt,
                prompt_hash,
                change_description,
                now,
                created_by,
                1,
            ),
        )
        
        # Actualizar versión en automata
        conn.execute(
            "UPDATE automata SET version = ?, updated_at = ? WHERE automaton_id = ?",
            (next_version, now, automaton_id)
        )
        
        # Registrar cambio
        change_id = f"CHANGE-{uuid.uuid4().hex[:8].upper()}"
        conn.execute(
            """
            INSERT INTO automata_changes (
                change_id, automaton_id, change_type, change_description,
                before_state, after_state, changed_by, changed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                change_id,
                automaton_id,
                "prompt_update",
                change_description,
                json.dumps({"version": next_version - 1}),
                json.dumps({"version": next_version, "prompt_preview": system_prompt[:200]}),
                created_by,
                now,
            ),
        )
        
        return {
            "version_id": version_id,
            "version_number": next_version,
            "automaton_id": automaton_id,
        }


def create_automaton_test_tool(
    automaton_id: str,
    test_name: str,
    test_description: str | None,
    test_type: str,
    test_scenario: dict[str, Any],
    expected_result: dict[str, Any] | None = None,
    created_by: str | None = None,
) -> dict:
    """Crea un test para el autómata."""
    import json
    with get_db() as conn:
        test_id = f"TEST-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(tz=timezone.utc).isoformat()
        created_by = created_by or "system"
        
        conn.execute(
            """
            INSERT INTO automata_tests (
                test_id, automaton_id, test_name, test_description, test_type,
                test_scenario, expected_result, is_active, created_at, updated_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                test_id,
                automaton_id,
                test_name,
                test_description,
                test_type,
                json.dumps(test_scenario, ensure_ascii=False),
                json.dumps(expected_result, ensure_ascii=False) if expected_result else None,
                1,
                now,
                now,
                created_by,
            ),
        )
        
        # Registrar cambio
        change_id = f"CHANGE-{uuid.uuid4().hex[:8].upper()}"
        conn.execute(
            """
            INSERT INTO automata_changes (
                change_id, automaton_id, change_type, change_description,
                before_state, after_state, changed_by, changed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                change_id,
                automaton_id,
                "test_add",
                f"Test '{test_name}' agregado",
                None,
                json.dumps({"test_name": test_name, "test_type": test_type}),
                created_by,
                now,
            ),
        )
        
        return {"test_id": test_id, "test_name": test_name}


def get_automaton_test_results_tool(
    automaton_id: str,
    test_id: str | None = None,
    limit: int = 50,
) -> dict:
    """Obtiene resultados de tests de un autómata."""
    import json
    with get_db() as conn:
        query = """
            SELECT * FROM automata_test_results
            WHERE automaton_id = ?
        """
        params = [automaton_id]
        
        if test_id:
            query += " AND test_id = ?"
            params.append(test_id)
        
        query += " ORDER BY executed_at DESC LIMIT ?"
        params.append(limit)
        
        cursor = conn.execute(query, params)
        results = []
        for row in cursor.fetchall():
            res = dict(row)
            res["actual_result"] = json.loads(res["actual_result"]) if res["actual_result"] else None
            res["metadata"] = json.loads(res["metadata_json"] or "{}")
            results.append(res)
        
        return {"results": results, "count": len(results)}


def get_automaton_metrics_tool(
    automaton_id: str,
    metric_type: str | None = None,
    limit: int = 50,
) -> dict:
    """Obtiene métricas de un autómata."""
    import json
    with get_db() as conn:
        query = """
            SELECT * FROM automata_metrics
            WHERE automaton_id = ?
        """
        params = [automaton_id]
        
        if metric_type:
            query += " AND metric_type = ?"
            params.append(metric_type)
        
        query += " ORDER BY evaluation_date DESC LIMIT ?"
        params.append(limit)
        
        cursor = conn.execute(query, params)
        metrics = []
        for row in cursor.fetchall():
            metric = dict(row)
            metric["metadata"] = json.loads(metric["metadata_json"] or "{}")
            metrics.append(metric)
        
        return {"metrics": metrics, "count": len(metrics)}


def get_automaton_changes_tool(
    automaton_id: str,
    limit: int = 50,
) -> dict:
    """Obtiene el historial de cambios de un autómata."""
    import json
    with get_db() as conn:
        cursor = conn.execute(
            """
            SELECT * FROM automata_changes
            WHERE automaton_id = ?
            ORDER BY changed_at DESC
            LIMIT ?
            """,
            (automaton_id, limit),
        )
        changes = []
        for row in cursor.fetchall():
            change = dict(row)
            change["before_state"] = json.loads(change["before_state"]) if change["before_state"] else None
            change["after_state"] = json.loads(change["after_state"]) if change["after_state"] else None
            changes.append(change)
        
        return {"changes": changes, "count": len(changes)}


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
            elif tool_name == "delete_flow":
                result = delete_flow_tool(flow_id=arguments["flow_id"])
            elif tool_name == "get_automaton":
                result = get_automaton_tool(automaton_id=arguments["automaton_id"])
            elif tool_name == "list_automata":
                result = list_automata_tool(
                    domain=arguments.get("domain"),
                    include_inactive=arguments.get("include_inactive", False),
                )
            elif tool_name == "create_automaton_version":
                result = create_automaton_version_tool(
                    automaton_id=arguments["automaton_id"],
                    system_prompt=arguments["system_prompt"],
                    change_description=arguments["change_description"],
                    created_by=arguments.get("created_by"),
                )
            elif tool_name == "create_automaton_test":
                result = create_automaton_test_tool(
                    automaton_id=arguments["automaton_id"],
                    test_name=arguments["test_name"],
                    test_description=arguments.get("test_description"),
                    test_type=arguments["test_type"],
                    test_scenario=arguments["test_scenario"],
                    expected_result=arguments.get("expected_result"),
                    created_by=arguments.get("created_by"),
                )
            elif tool_name == "get_automaton_test_results":
                result = get_automaton_test_results_tool(
                    automaton_id=arguments["automaton_id"],
                    test_id=arguments.get("test_id"),
                    limit=arguments.get("limit", 50),
                )
            elif tool_name == "get_automaton_metrics":
                result = get_automaton_metrics_tool(
                    automaton_id=arguments["automaton_id"],
                    metric_type=arguments.get("metric_type"),
                    limit=arguments.get("limit", 50),
                )
            elif tool_name == "get_automaton_changes":
                result = get_automaton_changes_tool(
                    automaton_id=arguments["automaton_id"],
                    limit=arguments.get("limit", 50),
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
    return {"status": "ok", "service": "mcp-booking-flow-server"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("BOOKING_FLOW_SERVER_PORT", "60006"))
    uvicorn.run(app, host="0.0.0.0", port=port)

