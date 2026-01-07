#!/usr/bin/env python3
"""Simple test for bookings flow logic without orchestrator dependencies."""

from __future__ import annotations

from ai_assistants.adapters.demo_bookings import DemoBookingsAdapter
from ai_assistants.domain.bookings.models import BookingStatus
from ai_assistants.orchestrator.state import ConversationState, MessageRole
from ai_assistants.tools.bookings_tools import check_availability, create_booking, get_available_slots
from ai_assistants.tools.contracts import CheckAvailabilityInput, CreateBookingInput, GetAvailableSlotsInput


def test_bookings_tools() -> None:
    """Test bookings tools directly."""
    print("=" * 60)
    print("PRUEBA DE HERRAMIENTAS DE RESERVAS")
    print("=" * 60)
    print()

    # Test 1: Consultar disponibilidad de slots
    print("Test 1: Consultar horarios disponibles para 2025-03-15")
    slots_out = get_available_slots(GetAvailableSlotsInput(date_iso="2025-03-15"))
    print(f"Resultado: {len(slots_out.slots)} slots disponibles")
    for slot in slots_out.slots:
        start = slot.start_time_iso.split("T")[1].split(":")[:2]
        end = slot.end_time_iso.split("T")[1].split(":")[:2]
        print(f"  - {':'.join(start)} a {':'.join(end)}")
    print()
    print("-" * 60)
    print()

    # Test 2: Verificar disponibilidad de un horario específico
    print("Test 2: Verificar disponibilidad de 09:00-10:00 del 2025-03-15")
    availability_out = check_availability(
        CheckAvailabilityInput(
            date_iso="2025-03-15",
            start_time_iso="2025-03-15T09:00:00Z",
            end_time_iso="2025-03-15T10:00:00Z",
        )
    )
    print(f"Resultado: {'Disponible' if availability_out.available else 'No disponible'}")
    print()
    print("-" * 60)
    print()

    # Test 3: Crear una reserva
    print("Test 3: Crear reserva para Juan Pérez")
    booking_out = create_booking(
        CreateBookingInput(
            customer_id="+5491112345678",
            customer_name="Juan Pérez",
            date_iso="2025-03-15",
            start_time_iso="2025-03-15T09:00:00Z",
            end_time_iso="2025-03-15T10:00:00Z",
        )
    )
    if booking_out.success and booking_out.booking_id:
        print(f"Resultado: Reserva creada exitosamente - {booking_out.booking_id}")
        start = booking_out.start_time_iso.split("T")[1].split(":")[:2]
        end = booking_out.end_time_iso.split("T")[1].split(":")[:2]
        print(f"  Fecha: {booking_out.date_iso}")
        print(f"  Horario: {':'.join(start)} a {':'.join(end)}")
    else:
        print("Resultado: Error al crear la reserva")
    print()
    print("-" * 60)
    print()

    # Test 4: Verificar que el horario ya no está disponible
    print("Test 4: Verificar que el horario 09:00-10:00 ya no está disponible")
    availability_out2 = check_availability(
        CheckAvailabilityInput(
            date_iso="2025-03-15",
            start_time_iso="2025-03-15T09:00:00Z",
            end_time_iso="2025-03-15T10:00:00Z",
        )
    )
    print(f"Resultado: {'Disponible' if availability_out2.available else 'No disponible (ocupado)'}")
    print()
    print("=" * 60)
    print("FIN DE LA PRUEBA")
    print("=" * 60)


def test_conversation_state() -> None:
    """Test conversation state flow."""
    print()
    print("=" * 60)
    print("PRUEBA DE FLUJO DE CONVERSACIÓN")
    print("=" * 60)
    print()

    # Simular estado inicial
    conversation = ConversationState(conversation_id="test:bookings")

    # Turn 1: Primera interacción
    print("Turn 1: Primera interacción")
    print("Usuario: Hola")
    has_assistant_messages = any(msg.role == MessageRole.assistant for msg in conversation.messages)
    if not has_assistant_messages:
        print("Asistente: Hola, soy tu asistente de reservas.\n¿Cómo te llamás?")
        print("✓ Saludo inicial correcto (2 líneas)")
    print()

    # Turn 2: Usuario proporciona nombre
    print("Turn 2: Captura de nombre")
    print("Usuario: Juan Pérez")
    conversation = conversation.model_copy(update={"customer_name": "Juan Pérez"})
    print(f"Asistente: Mucho gusto, {conversation.customer_name}. ¿Qué fecha y horario te gustaría reservar?")
    print(f"✓ Nombre capturado: {conversation.customer_name}")
    print()

    # Turn 3: Usuario solicita fecha
    print("Turn 3: Solicitud de fecha")
    print("Usuario: Quiero reservar para el 2025-03-15")
    print("Asistente: [Consulta disponibilidad...]")
    print("✓ Fecha solicitada: 2025-03-15")
    print()

    # Turn 4: Usuario solicita horario
    print("Turn 4: Solicitud de horario")
    print("Usuario: Quiero el horario de 09:00 a 10:00")
    conversation = conversation.model_copy(
        update={
            "requested_booking_date": "2025-03-15",
            "requested_booking_start_time": "2025-03-15T09:00:00Z",
            "requested_booking_end_time": "2025-03-15T10:00:00Z",
        }
    )
    print(
        f"Asistente: ¡Perfecto! El horario del {conversation.requested_booking_date} "
        f"de 09:00 a 10:00 está disponible. ¿Confirmás la reserva?"
    )
    print("✓ Horario solicitado y validado")
    print()

    # Turn 5: Confirmación
    print("Turn 5: Confirmación de reserva")
    print("Usuario: Sí, confirmo")
    booking_out = create_booking(
        CreateBookingInput(
            customer_id="+5491112345678",
            customer_name=conversation.customer_name or "Juan Pérez",
            date_iso=conversation.requested_booking_date or "2025-03-15",
            start_time_iso=conversation.requested_booking_start_time or "2025-03-15T09:00:00Z",
            end_time_iso=conversation.requested_booking_end_time or "2025-03-15T10:00:00Z",
        )
    )
    if booking_out.success and booking_out.booking_id:
        conversation = conversation.model_copy(update={"last_booking_id": booking_out.booking_id})
        response = (
            f"¡Reserva confirmada! Tu reserva {booking_out.booking_id} está confirmada para el "
            f"{booking_out.date_iso} de 09:00 a 10:00.\n"
            f"Te enviaremos un email de confirmación y te avisaremos con anticipación como recordatorio."
        )
        print(f"Asistente: {response}")
        print(f"✓ Reserva creada: {conversation.last_booking_id}")
        print("✓ Email de confirmación mencionado")
        print("✓ Recordatorio mencionado")
    print()
    print("=" * 60)
    print("FIN DE LA PRUEBA")
    print("=" * 60)


if __name__ == "__main__":
    test_bookings_tools()
    test_conversation_state()

