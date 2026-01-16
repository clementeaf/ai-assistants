#!/usr/bin/env python3
"""Script de prueba limpia para el modo autónomo."""

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

# Agregar el path del backend al PYTHONPATH
backend_path = Path(__file__).parent / "apps" / "backend"
sys.path.insert(0, str(backend_path))

# IMPORTANTE: Crear alias ANTES de importar cualquier módulo
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
    print("PRUEBA LIMPIA DEL MODO AUTÓNOMO")
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
        return
    
    if not llm_cfg.base_url or not llm_cfg.api_key or not llm_cfg.model:
        print("❌ Falta configuración LLM")
        return
    
    print("✅ Configuración completa\n")
    
    # Crear stores SQLite temporales (limpios, sin datos previos)
    import tempfile
    from dataclasses import replace
    from pathlib import Path
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite3')
    temp_db_path = Path(temp_db.name)
    temp_db.close()
    
    # Configurar stores con base de datos temporal
    store_config = load_sqlite_store_config()
    store_config = replace(store_config, path=temp_db_path)
    store = SqliteConversationStore(store_config)
    
    memory_config = load_sqlite_memory_store_config()
    memory_config = replace(memory_config, path=temp_db_path)
    memory_store = SqliteCustomerMemoryStore(memory_config)
    
    # Crear orchestrator
    orchestrator = Orchestrator(store=store, memory_store=memory_store)
    
    # Prueba: Flujo completo desde cero
    print("🧪 PRUEBA: Flujo completo desde cero")
    print("="*60)
    conversation_id = "test:clean:1"
    customer_id = "+5491112345678"
    
    # Paso 1: Saludo inicial
    print("\n[Paso 1] Usuario: Hola")
    print("─" * 60)
    result = orchestrator.run_turn(
        conversation_id=conversation_id,
        user_text="Hola",
        customer_id=customer_id
    )
    print(f"✅ Respuesta del asistente:")
    print(f"   {result.response_text}")
    print(f"📊 Estado:")
    print(f"   - Nombre guardado: {result.state.customer_name or 'Ninguno'}")
    print(f"   - Fecha solicitada: {result.state.requested_booking_date or 'Ninguna'}")
    
    # Paso 2: Proporcionar nombre
    print("\n[Paso 2] Usuario: Me llamo Juan Pérez")
    print("─" * 60)
    result = orchestrator.run_turn(
        conversation_id=conversation_id,
        user_text="Me llamo Juan Pérez",
        customer_id=customer_id
    )
    print(f"✅ Respuesta del asistente:")
    print(f"   {result.response_text}")
    print(f"📊 Estado:")
    print(f"   - Nombre guardado: {result.state.customer_name or 'Ninguno'}")
    print(f"   - Fecha solicitada: {result.state.requested_booking_date or 'Ninguna'}")
    
    # Paso 3: Solicitar reserva
    print("\n[Paso 3] Usuario: Quiero hacer una reserva")
    print("─" * 60)
    result = orchestrator.run_turn(
        conversation_id=conversation_id,
        user_text="Quiero hacer una reserva",
        customer_id=customer_id
    )
    print(f"✅ Respuesta del asistente:")
    print(f"   {result.response_text}")
    print(f"📊 Estado:")
    print(f"   - Nombre guardado: {result.state.customer_name or 'Ninguno'}")
    print(f"   - Fecha solicitada: {result.state.requested_booking_date or 'Ninguna'}")
    
    # Paso 4: Proporcionar fecha
    print("\n[Paso 4] Usuario: Para el 15 de enero")
    print("─" * 60)
    result = orchestrator.run_turn(
        conversation_id=conversation_id,
        user_text="Para el 15 de enero",
        customer_id=customer_id
    )
    print(f"✅ Respuesta del asistente:")
    print(f"   {result.response_text}")
    print(f"📊 Estado:")
    print(f"   - Nombre guardado: {result.state.customer_name or 'Ninguno'}")
    print(f"   - Fecha solicitada: {result.state.requested_booking_date or 'Ninguna'}")
    
    # Paso 5: Consultar horarios (debe usar fecha guardada)
    print("\n[Paso 5] Usuario: ¿Qué horarios hay disponibles?")
    print("─" * 60)
    result = orchestrator.run_turn(
        conversation_id=conversation_id,
        user_text="¿Qué horarios hay disponibles?",
        customer_id=customer_id
    )
    print(f"✅ Respuesta del asistente:")
    print(f"   {result.response_text}")
    print(f"📊 Estado:")
    print(f"   - Nombre guardado: {result.state.customer_name or 'Ninguno'}")
    print(f"   - Fecha solicitada: {result.state.requested_booking_date or 'Ninguna'}")
    
    print("\n" + "="*60)
    print("✅ Prueba completada")
    print("="*60 + "\n")
    
    # Restaurar directorio original
    os.chdir(original_cwd)

if __name__ == "__main__":
    main()
