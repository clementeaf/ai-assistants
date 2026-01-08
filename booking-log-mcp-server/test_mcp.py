#!/usr/bin/env python3
"""Test script for MCP Booking Log Server."""

import json
import sys

import requests

MCP_URL = "http://localhost:3003/mcp"


def call_mcp_tool(tool_name: str, arguments: dict) -> dict:
    """Call an MCP tool."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments,
        },
    }
    response = requests.post(MCP_URL, json=payload)
    response.raise_for_status()
    return response.json()


def test_create_booking_log():
    """Test creating a booking log entry."""
    print("\n📝 Test 1: Crear entrada en bitácora...")
    result = call_mcp_tool(
        "create_booking_log",
        {
            "booking_code": "BOOKING-TEST001",
            "customer_name": "Juan Pérez",
            "customer_id": "customer-001",
            "date_iso": "2025-01-15",
            "time_iso": "2025-01-15T10:00:00Z",
            "area_name": "Medicina",
            "specialty_name": "Cardiología",
            "professional_name": "Dr. María González",
            "observations": "Primera consulta, traer estudios previos",
        },
    )
    assert result.get("result") is not None, "Result should not be None"
    log = result["result"]["log"]
    assert log["booking_code"] == "BOOKING-TEST001", "Booking code should match"
    assert log["customer_name"] == "Juan Pérez", "Customer name should match"
    print(f"✅ Entrada creada: {log['log_id']}")
    return log["booking_code"]


def test_get_booking_log(booking_code: str):
    """Test getting a booking log entry."""
    print("\n🔍 Test 2: Obtener entrada por código...")
    result = call_mcp_tool("get_booking_log", {"booking_code": booking_code})
    assert result.get("result") is not None, "Result should not be None"
    log = result["result"]["log"]
    assert log is not None, "Log should not be None"
    assert log["booking_code"] == booking_code, "Booking code should match"
    print(f"✅ Entrada encontrada: {log['log_id']}")
    print(f"   Cliente: {log['customer_name']}")
    print(f"   Profesional: {log['professional_name']}")


def test_list_booking_logs():
    """Test listing booking logs."""
    print("\n📋 Test 3: Listar entradas...")
    result = call_mcp_tool("list_booking_logs", {"limit": 10})
    assert result.get("result") is not None, "Result should not be None"
    logs = result["result"]["logs"]
    assert isinstance(logs, list), "Logs should be a list"
    print(f"✅ Encontradas {len(logs)} entradas")
    if logs:
        print(f"   Primera entrada: {logs[0]['booking_code']}")


def test_list_booking_logs_filtered():
    """Test listing booking logs with filters."""
    print("\n🔎 Test 4: Listar entradas con filtros...")
    result = call_mcp_tool(
        "list_booking_logs",
        {
            "customer_id": "customer-001",
            "limit": 10,
        },
    )
    assert result.get("result") is not None, "Result should not be None"
    logs = result["result"]["logs"]
    assert isinstance(logs, list), "Logs should be a list"
    print(f"✅ Encontradas {len(logs)} entradas para customer-001")


def test_update_booking_log(booking_code: str):
    """Test updating a booking log entry."""
    print("\n✏️  Test 5: Actualizar entrada...")
    result = call_mcp_tool(
        "update_booking_log",
        {
            "booking_code": booking_code,
            "observations": "Consulta completada, paciente derivado a especialista",
        },
    )
    assert result.get("result") is not None, "Result should not be None"
    log = result["result"]["log"]
    assert log is not None, "Log should not be None"
    assert "derivado" in log["observations"], "Observations should be updated"
    print(f"✅ Entrada actualizada: {log['log_id']}")
    print(f"   Nuevas observaciones: {log['observations']}")


def test_delete_booking_log(booking_code: str):
    """Test deleting a booking log entry."""
    print("\n🗑️  Test 6: Eliminar entrada...")
    result = call_mcp_tool("delete_booking_log", {"booking_code": booking_code})
    assert result.get("result") is not None, "Result should not be None"
    success = result["result"]["success"]
    assert success is True, "Delete should succeed"
    print(f"✅ Entrada eliminada: {booking_code}")

    # Verify deletion
    result = call_mcp_tool("get_booking_log", {"booking_code": booking_code})
    assert result.get("result") is not None, "Result should not be None"
    log = result["result"]["log"]
    assert log is None, "Log should be None after deletion"
    print("✅ Verificación: entrada no encontrada después de eliminar")


def main():
    """Run all tests."""
    print("🧪 Iniciando pruebas del servidor MCP Booking Log...")
    print(f"📍 URL: {MCP_URL}")

    try:
        # Health check
        response = requests.get("http://localhost:3003/health")
        response.raise_for_status()
        print("✅ Servidor disponible")

        booking_code = test_create_booking_log()
        test_get_booking_log(booking_code)
        test_list_booking_logs()
        test_list_booking_logs_filtered()
        test_update_booking_log(booking_code)
        test_delete_booking_log(booking_code)

        print("\n🎉 ¡Todas las pruebas pasaron!")
        return 0
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: No se pudo conectar al servidor")
        print("   Asegúrate de que el servidor esté corriendo en http://localhost:3003")
        return 1
    except AssertionError as e:
        print(f"\n❌ Error en prueba: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

