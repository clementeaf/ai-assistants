"""
Gestión completa de autómatas: versionado, tests, métricas y cambios.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any


def _migrate_flows_to_automata(conn: sqlite3.Connection) -> None:
    """Migra flows existentes a la tabla automata si no existen."""
    # Verificar si hay flows sin correspondiente en automata
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


def create_automaton(
    conn: sqlite3.Connection,
    name: str,
    description: str | None,
    domain: str,
    system_prompt: str,
    created_by: str | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Crea un nuevo autómata con su versión inicial."""
    automaton_id = f"AUTOMATON-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(tz=timezone.utc).isoformat()
    created_by = created_by or "system"
    
    # Crear autómata
    conn.execute(
        """
        INSERT INTO automata (
            automaton_id, name, description, domain, version, is_active,
            created_at, updated_at, created_by, tags, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            automaton_id,
            name,
            description,
            domain,
            1,
            1,
            now,
            now,
            created_by,
            json.dumps(tags or []),
            json.dumps({}),
        ),
    )
    
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
            "Versión inicial",
            now,
            created_by,
            1,
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
            "creation",
            f"Autómata '{name}' creado",
            None,
            json.dumps({"name": name, "domain": domain, "version": 1}),
            created_by,
            now,
        ),
    )
    
    return {
        "automaton_id": automaton_id,
        "name": name,
        "version_id": version_id,
        "version_number": 1,
    }


def create_automaton_version(
    conn: sqlite3.Connection,
    automaton_id: str,
    system_prompt: str,
    change_description: str,
    created_by: str | None = None,
) -> dict[str, Any]:
    """Crea una nueva versión del prompt del autómata."""
    created_by = created_by or "system"
    now = datetime.now(tz=timezone.utc).isoformat()
    
    # Obtener versión actual
    cursor = conn.execute(
        """
        SELECT MAX(version_number) as max_version FROM automata_versions
        WHERE automaton_id = ?
        """
    )
    row = cursor.fetchone()
    next_version = (row["max_version"] or 0) + 1
    
    # Desactivar versión actual
    conn.execute(
        """
        UPDATE automata_versions SET is_current = 0
        WHERE automaton_id = ? AND is_current = 1
        """
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
        """
        UPDATE automata SET version = ?, updated_at = ?
        WHERE automaton_id = ?
        """,
        (next_version, now, automaton_id),
    )
    
    # Obtener prompt anterior para el cambio
    cursor = conn.execute(
        """
        SELECT system_prompt FROM automata_versions
        WHERE automaton_id = ? AND version_number = ?
        """,
        (automaton_id, next_version - 1),
    )
    old_prompt = cursor.fetchone()["system_prompt"] if cursor.fetchone() else None
    
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
            json.dumps({"prompt": old_prompt, "version": next_version - 1}) if old_prompt else None,
            json.dumps({"prompt": system_prompt[:200], "version": next_version}),
            created_by,
            now,
        ),
    )
    
    return {
        "version_id": version_id,
        "version_number": next_version,
        "automaton_id": automaton_id,
    }


def add_automaton_tool(
    conn: sqlite3.Connection,
    automaton_id: str,
    tool_name: str,
    tool_description: str | None,
    tool_input_schema: dict[str, Any] | None = None,
    tool_output_schema: dict[str, Any] | None = None,
    is_required: bool = True,
) -> dict[str, Any]:
    """Agrega una herramienta/función usada por el autómata."""
    tool_id = f"TOOL-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(tz=timezone.utc).isoformat()
    
    conn.execute(
        """
        INSERT INTO automata_tools (
            tool_id, automaton_id, tool_name, tool_description,
            tool_input_schema, tool_output_schema, is_required, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            tool_id,
            automaton_id,
            tool_name,
            tool_description,
            json.dumps(tool_input_schema) if tool_input_schema else None,
            json.dumps(tool_output_schema) if tool_output_schema else None,
            1 if is_required else 0,
            now,
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
            "tool_add",
            f"Herramienta '{tool_name}' agregada",
            None,
            json.dumps({"tool_name": tool_name, "is_required": is_required}),
            "system",
            now,
        ),
    )
    
    return {"tool_id": tool_id, "tool_name": tool_name}


def create_automaton_test(
    conn: sqlite3.Connection,
    automaton_id: str,
    test_name: str,
    test_description: str | None,
    test_type: str,
    test_scenario: dict[str, Any],
    expected_result: dict[str, Any] | None = None,
    created_by: str | None = None,
) -> dict[str, Any]:
    """Crea un test para el autómata."""
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


def record_test_result(
    conn: sqlite3.Connection,
    test_id: str,
    automaton_id: str,
    version_id: str | None,
    execution_status: str,
    actual_result: dict[str, Any] | None = None,
    execution_time_ms: int | None = None,
    error_message: str | None = None,
    error_stack: str | None = None,
    executed_by: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Registra el resultado de la ejecución de un test."""
    result_id = f"RESULT-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(tz=timezone.utc).isoformat()
    executed_by = executed_by or "system"
    
    conn.execute(
        """
        INSERT INTO automata_test_results (
            result_id, test_id, automaton_id, version_id, execution_status,
            actual_result, execution_time_ms, error_message, error_stack,
            executed_at, executed_by, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            result_id,
            test_id,
            automaton_id,
            version_id,
            execution_status,
            json.dumps(actual_result, ensure_ascii=False) if actual_result else None,
            execution_time_ms,
            error_message,
            error_stack,
            now,
            executed_by,
            json.dumps(metadata, ensure_ascii=False) if metadata else None,
        ),
    )
    
    return {"result_id": result_id, "execution_status": execution_status}


def record_automaton_metric(
    conn: sqlite3.Connection,
    automaton_id: str,
    metric_type: str,
    metric_value: float,
    metric_unit: str | None = None,
    version_id: str | None = None,
    sample_size: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Registra una métrica de evaluación del autómata."""
    metric_id = f"METRIC-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(tz=timezone.utc).isoformat()
    
    conn.execute(
        """
        INSERT INTO automata_metrics (
            metric_id, automaton_id, version_id, metric_type, metric_value,
            metric_unit, evaluation_date, sample_size, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            metric_id,
            automaton_id,
            version_id,
            metric_type,
            metric_value,
            metric_unit,
            now,
            sample_size,
            json.dumps(metadata, ensure_ascii=False) if metadata else None,
        ),
    )
    
    return {"metric_id": metric_id, "metric_type": metric_type, "metric_value": metric_value}


def get_automaton_full_info(conn: sqlite3.Connection, automaton_id: str) -> dict[str, Any]:
    """Obtiene información completa del autómata incluyendo versiones, tools, tests y métricas."""
    # Información del autómata
    cursor = conn.execute(
        """
        SELECT * FROM automata WHERE automaton_id = ?
        """,
        (automaton_id,),
    )
    automaton = cursor.fetchone()
    if not automaton:
        return {}
    
    result = dict(automaton)
    result["tags"] = json.loads(automaton["tags"] or "[]")
    result["metadata"] = json.loads(automaton["metadata_json"] or "{}")
    
    # Versiones
    cursor = conn.execute(
        """
        SELECT * FROM automata_versions
        WHERE automaton_id = ?
        ORDER BY version_number DESC
        """
    )
    versions = [dict(row) for row in cursor.fetchall()]
    result["versions"] = versions
    
    # Versión actual
    current_version = next((v for v in versions if v["is_current"] == 1), None)
    result["current_version"] = current_version
    
    # Herramientas
    cursor = conn.execute(
        """
        SELECT * FROM automata_tools
        WHERE automaton_id = ?
        ORDER BY tool_name
        """
    )
    tools = []
    for row in cursor.fetchall():
        tool = dict(row)
        tool["input_schema"] = json.loads(tool["tool_input_schema"] or "{}")
        tool["output_schema"] = json.loads(tool["tool_output_schema"] or "{}")
        tools.append(tool)
    result["tools"] = tools
    
    # Tests
    cursor = conn.execute(
        """
        SELECT * FROM automata_tests
        WHERE automaton_id = ? AND is_active = 1
        ORDER BY created_at DESC
        """
    )
    tests = []
    for row in cursor.fetchall():
        test = dict(row)
        test["scenario"] = json.loads(test["test_scenario"])
        test["expected_result"] = json.loads(test["expected_result"]) if test["expected_result"] else None
        tests.append(test)
    result["tests"] = tests
    
    # Últimos resultados de tests
    cursor = conn.execute(
        """
        SELECT * FROM automata_test_results
        WHERE automaton_id = ?
        ORDER BY executed_at DESC
        LIMIT 10
        """
    )
    test_results = []
    for row in cursor.fetchall():
        res = dict(row)
        res["actual_result"] = json.loads(res["actual_result"]) if res["actual_result"] else None
        res["metadata"] = json.loads(res["metadata_json"] or "{}")
        test_results.append(res)
    result["recent_test_results"] = test_results
    
    # Métricas recientes
    cursor = conn.execute(
        """
        SELECT * FROM automata_metrics
        WHERE automaton_id = ?
        ORDER BY evaluation_date DESC
        LIMIT 20
        """
    )
    metrics = []
    for row in cursor.fetchall():
        metric = dict(row)
        metric["metadata"] = json.loads(metric["metadata_json"] or "{}")
        metrics.append(metric)
    result["metrics"] = metrics
    
    # Historial de cambios recientes
    cursor = conn.execute(
        """
        SELECT * FROM automata_changes
        WHERE automaton_id = ?
        ORDER BY changed_at DESC
        LIMIT 20
        """
    )
    changes = []
    for row in cursor.fetchall():
        change = dict(row)
        change["before_state"] = json.loads(change["before_state"]) if change["before_state"] else None
        change["after_state"] = json.loads(change["after_state"]) if change["after_state"] else None
        changes.append(change)
    result["recent_changes"] = changes
    
    return result
