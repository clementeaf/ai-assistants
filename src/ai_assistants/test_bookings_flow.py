#!/usr/bin/env python3
"""Test script for bookings flow using the orchestrator."""

from __future__ import annotations

from ai_assistants.orchestrator.runtime import Orchestrator
from ai_assistants.persistence.sqlite_store import SqliteConversationStore, SqliteStoreConfig
from ai_assistants.persistence.sqlite_memory_store import SqliteCustomerMemoryStore, SqliteMemoryStoreConfig


def test_bookings_flow() -> None:
    """Test the complete bookings flow."""
    store_config = SqliteStoreConfig(db_path=":memory:")
    store = SqliteConversationStore(store_config)
    memory_config = SqliteMemoryStoreConfig(db_path=":memory:")
    memory_store = SqliteCustomerMemoryStore(memory_config)
    orchestrator = Orchestrator(store=store, memory_store=memory_store)

    conversation_id = "test:bookings_flow"
    customer_id = "+5491112345678"

    print("=" * 60)
    print("PRUEBA DE FLUJO DE RESERVAS (Orchestrator)")
    print("=" * 60)
    print()

    # Turn 1: Primera interacción - Saludo
    print("Usuario: Hola")
    print()
    result1 = orchestrator.run_turn(conversation_id=conversation_id, user_text="Hola", customer_id=customer_id)
    print(f"Asistente: {result1.response_text}")
    print()
    print("-" * 60)
    print()

    # Turn 2: Usuario proporciona nombre
    print("Usuario: Juan Pérez")
    print()
    result2 = orchestrator.run_turn(conversation_id=conversation_id, user_text="Juan Pérez", customer_id=customer_id)
    print(f"Asistente: {result2.response_text}")
    print()
    print("-" * 60)
    print()

    # Turn 3: Usuario pregunta por disponibilidad de una fecha
    print("Usuario: Quiero reservar para el 2025-03-15")
    print()
    result3 = orchestrator.run_turn(
        conversation_id=conversation_id, user_text="Quiero reservar para el 2025-03-15", customer_id=customer_id
    )
    print(f"Asistente: {result3.response_text}")
    print()
    print("-" * 60)
    print()

    # Turn 4: Usuario solicita un horario específico
    print("Usuario: Quiero el horario de 09:00 a 10:00")
    print()
    result4 = orchestrator.run_turn(
        conversation_id=conversation_id,
        user_text="Quiero el horario de 09:00 a 10:00 del 2025-03-15",
        customer_id=customer_id,
    )
    print(f"Asistente: {result4.response_text}")
    print()
    print("-" * 60)
    print()

    # Turn 5: Usuario confirma la reserva
    print("Usuario: Sí, confirmo")
    print()
    result5 = orchestrator.run_turn(conversation_id=conversation_id, user_text="Sí, confirmo", customer_id=customer_id)
    print(f"Asistente: {result5.response_text}")
    print()
    print("=" * 60)
    print("FIN DE LA PRUEBA")
    print("=" * 60)


if __name__ == "__main__":
    test_bookings_flow()

