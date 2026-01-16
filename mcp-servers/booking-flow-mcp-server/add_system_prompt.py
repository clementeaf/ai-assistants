#!/usr/bin/env python3
"""Script para agregar el stage system_prompt a flujos de bookings existentes."""

from __future__ import annotations

import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(os.getenv("BOOKING_FLOW_DB_PATH", "booking_flow.db"))


def load_system_prompt() -> str | None:
    """Carga el prompt del sistema desde autonomous_system.txt."""
    try:
        # Buscar el archivo en diferentes ubicaciones posibles
        script_dir = Path(__file__).resolve().parent
        possible_paths = [
            script_dir.parents[1] / "apps" / "backend" / "prompts" / "autonomous_system.txt",
            script_dir / ".." / ".." / "apps" / "backend" / "prompts" / "autonomous_system.txt",
            Path.cwd() / "apps" / "backend" / "prompts" / "autonomous_system.txt",
            Path.cwd() / "mcp-servers" / ".." / "apps" / "backend" / "prompts" / "autonomous_system.txt",
        ]
        
        for path in possible_paths:
            abs_path = path.resolve()
            if abs_path.exists():
                print(f"✓ Encontrado prompt en: {abs_path}")
                return abs_path.read_text(encoding="utf-8")
        
        print("⚠ No se encontró el archivo autonomous_system.txt")
        return None
    except Exception as e:
        print(f"✗ Error al cargar el prompt: {e}")
        return None


def add_system_prompt_to_flows() -> None:
    """Agrega el stage system_prompt a todos los flujos de bookings que no lo tengan."""
    if not DB_PATH.exists():
        print(f"✗ La base de datos no existe en: {DB_PATH}")
        print("  El servidor MCP debe haberse ejecutado al menos una vez para crear la BD.")
        return
    
    system_prompt_text = load_system_prompt()
    if not system_prompt_text:
        print("✗ No se pudo cargar el prompt del sistema. Abortando.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    try:
        # Obtener todos los flujos de bookings activos
        cursor = conn.execute("SELECT flow_id, name FROM flows WHERE domain = 'bookings' AND is_active = 1")
        flows = cursor.fetchall()
        
        if not flows:
            print("⚠ No se encontraron flujos de bookings activos.")
            return
        
        print(f"✓ Encontrados {len(flows)} flujo(s) de bookings:")
        for flow in flows:
            print(f"  - {flow['name']} (ID: {flow['flow_id']})")
        
        now = datetime.now(tz=timezone.utc).isoformat()
        added_count = 0
        
        for flow_row in flows:
            flow_id = flow_row["flow_id"]
            flow_name = flow_row["name"]
            
            # Verificar si ya tiene un stage system_prompt
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM flow_stages WHERE flow_id = ? AND stage_type = 'system_prompt'",
                (flow_id,)
            )
            if cursor.fetchone()["count"] > 0:
                print(f"  ⏭ {flow_name}: Ya tiene stage system_prompt, omitiendo.")
                continue
            
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
            
            print(f"  ✓ {flow_name}: Agregado stage system_prompt (orden: {next_order})")
            added_count += 1
        
        conn.commit()
        print(f"\n✓ Proceso completado. Se agregaron {added_count} stage(s) system_prompt.")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Agregando stage system_prompt a flujos de bookings")
    print("=" * 60)
    print(f"Base de datos: {DB_PATH.resolve()}")
    print()
    
    add_system_prompt_to_flows()
