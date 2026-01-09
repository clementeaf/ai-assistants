#!/usr/bin/env python3
"""Test script for MCP LLM Server."""

import json
import os
import sys

import requests

MCP_URL = os.getenv("LLM_MCP_TEST_URL", "http://localhost:3004/mcp")


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


def test_chat_completion():
    """Test chat completion."""
    print("\n💬 Test 1: Chat completion básico...")
    result = call_mcp_tool(
        "chat_completion",
        {
            "system": "Eres un asistente útil y conciso.",
            "user": "¿Cuál es la capital de Francia? Responde en una sola palabra.",
        },
    )
    assert result.get("result") is not None, "Result should not be None"
    content = result["result"]["content"]
    assert isinstance(content, str), "Content should be a string"
    assert len(content) > 0, "Content should not be empty"
    print(f"✅ Respuesta recibida: {content[:100]}...")
    print(f"   Modelo: {result['result'].get('model', 'unknown')}")
    print(f"   Tiempo: {result['result'].get('elapsed_seconds', 0)}s")


def test_chat_completion_with_temperature():
    """Test chat completion with custom temperature."""
    print("\n🌡️  Test 2: Chat completion con temperatura...")
    result = call_mcp_tool(
        "chat_completion",
        {
            "system": "Eres un asistente creativo.",
            "user": "Dame un nombre creativo para una cafetería.",
            "temperature": 0.8,
        },
    )
    assert result.get("result") is not None, "Result should not be None"
    content = result["result"]["content"]
    assert isinstance(content, str), "Content should be a string"
    print(f"✅ Respuesta creativa: {content[:100]}...")


def test_chat_completion_with_model():
    """Test chat completion with specific model."""
    print("\n🤖 Test 3: Chat completion con modelo específico...")
    result = call_mcp_tool(
        "chat_completion",
        {
            "system": "Eres un asistente técnico.",
            "user": "Explica qué es Python en una frase.",
            "model": "gpt-4o-mini",
        },
    )
    assert result.get("result") is not None, "Result should not be None"
    content = result["result"]["content"]
    assert isinstance(content, str), "Content should be a string"
    print(f"✅ Respuesta técnica: {content[:100]}...")


def test_chat_completion_booking_scenario():
    """Test chat completion with booking scenario."""
    print("\n📅 Test 4: Escenario de reservas...")
    result = call_mcp_tool(
        "chat_completion",
        {
            "system": "Eres un asistente de reservas. Responde de forma profesional y amable.",
            "user": "El usuario pregunta: 'Quiero una reserva para mañana a las 3pm'. ¿Qué información adicional necesitas?",
        },
    )
    assert result.get("result") is not None, "Result should not be None"
    content = result["result"]["content"]
    assert isinstance(content, str), "Content should be a string"
    print(f"✅ Respuesta de reservas: {content[:150]}...")


def main():
    """Run all tests."""
    print("🧪 Iniciando pruebas del servidor MCP LLM...")
    print(f"📍 URL: {MCP_URL}")

    try:
        # Health check
        base_url = MCP_URL.replace("/mcp", "")
        response = requests.get(f"{base_url}/health")
        response.raise_for_status()
        health = response.json()
        print(f"✅ Servidor disponible")
        print(f"   Modelo: {health.get('model', 'unknown')}")
        print(f"   Base URL: {health.get('base_url', 'unknown')}")

        test_chat_completion()
        test_chat_completion_with_temperature()
        test_chat_completion_with_model()
        test_chat_completion_booking_scenario()

        print("\n🎉 ¡Todas las pruebas pasaron!")
        return 0
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: No se pudo conectar al servidor")
        print(f"   Asegúrate de que el servidor esté corriendo en {MCP_URL.replace('/mcp', '')}")
        print("   Y que las variables de entorno LLM_MCP_* estén configuradas")
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

