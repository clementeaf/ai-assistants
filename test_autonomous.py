#!/usr/bin/env python3
"""Script de prueba para el modo autónomo."""

import os
import sys
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

# Agregar el path del backend al PYTHONPATH (necesario para imports)
backend_path = Path(__file__).parent / "apps" / "backend"
sys.path.insert(0, str(backend_path))

# IMPORTANTE: Crear alias ANTES de importar cualquier módulo que use 'ai_assistants'
# El código usa 'ai_assistants' pero el directorio es 'backend'
# Necesitamos importar el paquete backend como ai_assistants
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

def main():
    print("\n" + "="*60)
    print("PRUEBA DEL MODO AUTÓNOMO")
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
    
    # Crear stores temporales
    db_path = Path(".data/test_autonomous.sqlite3")
    db_path.parent.mkdir(exist_ok=True)
    
    store = SqliteConversationStore(load_sqlite_store_config())
    memory_store = SqliteCustomerMemoryStore(load_sqlite_memory_store_config())
    
    # Crear orchestrator
    orchestrator = Orchestrator(store=store, memory_store=memory_store)
    
    # Prueba 1: Flujo completo de reserva
    print("🧪 Prueba 1: Flujo completo de reserva")
    print("-" * 60)
    conversation_id = "test:autonomous:booking:1"
    customer_id = "+5491112345678"
    
    # Paso 1: Saludo inicial
    print("\n[1] Usuario: Hola")
    print("Procesando...")
    try:
        result = orchestrator.run_turn(
            conversation_id=conversation_id,
            user_text="Hola",
            customer_id=customer_id
        )
        print(f"✅ Respuesta: {result.response_text}")
        print(f"   Nombre en conversación: {result.state.customer_name}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Paso 2: Proporcionar nombre
    print("\n[2] Usuario: Me llamo Juan Pérez")
    print("Procesando...")
    try:
        result = orchestrator.run_turn(
            conversation_id=conversation_id,
            user_text="Me llamo Juan Pérez",
            customer_id=customer_id
        )
        print(f"✅ Respuesta: {result.response_text}")
        print(f"   Nombre guardado: {result.state.customer_name}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Paso 3: Solicitar reserva
    print("\n[3] Usuario: Quiero hacer una reserva")
    print("Procesando...")
    try:
        result = orchestrator.run_turn(
            conversation_id=conversation_id,
            user_text="Quiero hacer una reserva",
            customer_id=customer_id
        )
        print(f"✅ Respuesta: {result.response_text}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Paso 4: Proporcionar fecha
    print("\n[4] Usuario: Para el 15 de enero")
    print("Procesando...")
    try:
        result = orchestrator.run_turn(
            conversation_id=conversation_id,
            user_text="Para el 15 de enero",
            customer_id=customer_id
        )
        print(f"✅ Respuesta: {result.response_text}")
        print(f"   Fecha solicitada: {result.state.requested_booking_date}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Paso 5: Consultar horarios disponibles
    print("\n[5] Usuario: ¿Qué horarios hay disponibles?")
    print("Procesando...")
    try:
        result = orchestrator.run_turn(
            conversation_id=conversation_id,
            user_text="¿Qué horarios hay disponibles?",
            customer_id=customer_id
        )
        print(f"✅ Respuesta: {result.response_text}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Prueba 2: Consulta de reservas existentes
    print("\n" + "="*60)
    print("🧪 Prueba 2: Consulta de reservas")
    print("-" * 60)
    
    conversation_id2 = "test:autonomous:list:1"
    
    print("\n[1] Usuario: Hola, me llamo María García")
    print("Procesando...")
    try:
        result = orchestrator.run_turn(
            conversation_id=conversation_id2,
            user_text="Hola, me llamo María García",
            customer_id="+5491198765432"
        )
        print(f"✅ Respuesta: {result.response_text}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n[2] Usuario: ¿Cuáles son mis reservas?")
    print("Procesando...")
    try:
        result = orchestrator.run_turn(
            conversation_id=conversation_id2,
            user_text="¿Cuáles son mis reservas?",
            customer_id="+5491198765432"
        )
        print(f"✅ Respuesta: {result.response_text}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "="*60)
    print("✅ Pruebas completadas")
    print("="*60 + "\n")
    
    # Restaurar directorio original
    os.chdir(original_cwd)

if __name__ == "__main__":
    main()
