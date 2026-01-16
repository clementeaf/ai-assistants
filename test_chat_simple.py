#!/usr/bin/env python3
"""Script para probar la comunicación simulando frontend-backend (sin WebSocket)."""

import os
import sys
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Cargar .env
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print("✅ Archivo .env cargado")
else:
    print("❌ Archivo .env no encontrado")
    sys.exit(1)

# Agregar el path del backend al PYTHONPATH
backend_path = Path(__file__).parent / "apps" / "backend"
sys.path.insert(0, str(backend_path))

# IMPORTANTE: Crear alias ANTES de importar cualquier módulo que use 'ai_assistants'
import importlib.util
spec = importlib.util.spec_from_file_location("backend", backend_path / "__init__.py")
backend = importlib.util.module_from_spec(spec)
sys.modules["ai_assistants"] = backend
spec.loader.exec_module(backend)

# Cambiar al directorio del backend
original_cwd = os.getcwd()
os.chdir(backend_path)

from ai_assistants.routing.autonomous_config import load_autonomous_config
from ai_assistants.config.llm_config import load_llm_config
from ai_assistants.orchestrator.runtime import Orchestrator
from ai_assistants.persistence.sqlite_store import SqliteConversationStore, load_sqlite_store_config
from ai_assistants.persistence.sqlite_memory_store import SqliteCustomerMemoryStore, load_sqlite_memory_store_config
from dataclasses import replace

def main():
    print("\n" + "="*60)
    print("PRUEBA DE COMUNICACIÓN (SIMULANDO FRONTEND-BACKEND)")
    print("="*60 + "\n")

    # Verificar configuración
    autonomous_cfg = load_autonomous_config()
    llm_cfg = load_llm_config()

    print("📋 Configuración:")
    print(f"  Modo Autónomo: {'✅ HABILITADO' if autonomous_cfg.enabled else '❌ DESHABILITADO'}")
    print(f"  Max History: {autonomous_cfg.max_history_messages}")
    print(f"  LLM Base URL: {llm_cfg.base_url}")
    print(f"  LLM Model: {llm_cfg.model}")
    print(f"  LLM API Key: {'✅ CONFIGURADA' if llm_cfg.api_key and llm_cfg.api_key != 'sk-your-key' else '❌ NO CONFIGURADA'}")
    print()

    if not autonomous_cfg.enabled:
        print("❌ El modo autónomo no está habilitado")
        print("   Cambia AI_ASSISTANTS_AUTONOMOUS_ENABLED=1 en .env")
        return

    if not llm_cfg.base_url or not llm_cfg.api_key or not llm_cfg.model:
        print("❌ Falta configuración LLM")
        return

    if llm_cfg.api_key == "sk-your-key":
        print("❌ La API key no está configurada (sigue siendo el placeholder)")
        return

    print("✅ Configuración completa\n")

    # Crear stores temporales en un archivo temporal para cada ejecución
    with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as temp_db:
        temp_db_path = Path(temp_db.name)

    try:
        # Configurar stores
        store_config = load_sqlite_store_config()
        store_config = replace(store_config, path=temp_db_path)
        store = SqliteConversationStore(store_config)

        memory_store_config = load_sqlite_memory_store_config()
        memory_store_config = replace(memory_store_config, path=temp_db_path)
        memory_store = SqliteCustomerMemoryStore(memory_store_config)

        # Crear orchestrator
        orchestrator = Orchestrator(store=store, memory_store=memory_store)

        conversation_id = "test:chat:simple:1"
        customer_id = "+5491112345678"

        print("🧪 PRUEBA: Enviar 'Hola'")
        print("="*60 + "\n")

        # Simular mensaje del frontend
        print(f"[Frontend] Enviando mensaje: 'Hola'")
        print(f"  Conversation ID: {conversation_id}")
        print(f"  Customer ID: {customer_id}")
        print()

        # Procesar mensaje (simula lo que hace el WebSocket endpoint)
        result = orchestrator.run_turn(
            conversation_id=conversation_id,
            user_text="Hola",
            customer_id=customer_id
        )

        # Simular respuesta al frontend
        print(f"[Backend] Respuesta generada:")
        print(f"  Type: assistant_message")
        print(f"  Text: {result.response_text}")
        print(f"  Conversation ID: {result.conversation_id}")
        print()

        # Verificar respuesta esperada
        expected_response = "¡Hola! Buenos días, soy el Asistente IA, ¿qué fecha y hora quisieras consultar para reservar?"
        actual_response = result.response_text

        print("="*60)
        print("RESULTADO:")
        print("="*60)
        print(f"✅ Respuesta recibida: {actual_response}")
        print()
        
        if expected_response == actual_response:
            print("✅ ✅ ✅ RESULTADO: CORRECTO - La respuesta coincide exactamente")
        elif expected_response in actual_response:
            print("⚠️  RESULTADO: PARCIAL - La respuesta contiene el texto esperado pero no es exacta")
            print(f"   Esperado: {expected_response}")
            print(f"   Recibido: {actual_response}")
        else:
            print("❌ RESULTADO: INCORRECTO - La respuesta NO coincide")
            print(f"   Esperado: {expected_response}")
            print(f"   Recibido: {actual_response}")
        
        print("="*60 + "\n")

        # Prueba 2: Segundo "Hola" para verificar consistencia
        print("🧪 PRUEBA 2: Enviar 'Hola' (segunda vez)")
        print("="*60 + "\n")

        print(f"[Frontend] Enviando mensaje: 'Hola'")
        print()

        result2 = orchestrator.run_turn(
            conversation_id=conversation_id,
            user_text="Hola",
            customer_id=customer_id
        )

        print(f"[Backend] Respuesta generada:")
        print(f"  Text: {result2.response_text}")
        print()

        actual_response2 = result2.response_text
        print("="*60)
        print("RESULTADO:")
        print("="*60)
        print(f"✅ Respuesta recibida: {actual_response2}")
        print()
        
        if expected_response == actual_response2:
            print("✅ ✅ ✅ RESULTADO: CORRECTO - La respuesta coincide exactamente")
        elif expected_response in actual_response2:
            print("⚠️  RESULTADO: PARCIAL - La respuesta contiene el texto esperado pero no es exacta")
        else:
            print("❌ RESULTADO: INCORRECTO - La respuesta NO coincide")
            print(f"   Esperado: {expected_response}")
            print(f"   Recibido: {actual_response2}")
        
        print("="*60 + "\n")

    finally:
        # Limpiar archivo temporal
        if temp_db_path.exists():
            temp_db_path.unlink()
            if temp_db_path.with_suffix(".sqlite3-wal").exists():
                temp_db_path.with_suffix(".sqlite3-wal").unlink()
            if temp_db_path.with_suffix(".sqlite3-shm").exists():
                temp_db_path.with_suffix(".sqlite3-shm").unlink()

    # Restaurar directorio original
    os.chdir(original_cwd)

if __name__ == "__main__":
    main()
