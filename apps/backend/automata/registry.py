"""
Registry dinámico de autómatas disponibles.
Proporciona información sobre dominios, herramientas y metadata para el frontend.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pathlib import Path


@dataclass
class AutomatonMetadata:
    """Metadata de un autómata para el frontend."""

    domain: str
    display_name: str
    description: str
    activation_code: str
    tools: list[dict[str, Any]]
    is_enabled: bool


def get_automata_registry() -> dict[str, AutomatonMetadata]:
    """Obtiene el registro de todos los autómatas disponibles dinámicamente."""
    registry: dict[str, AutomatonMetadata] = {}
    
    # Obtener información de cada autómata desde sus carpetas
    automata_dir = Path(__file__).parent
    
    # bookings
    if (automata_dir / "bookings").exists():
        registry["bookings"] = AutomatonMetadata(
            domain="bookings",
            display_name="Asistente de Reservas con Google Calendar",
            description="Autómata que gestiona reservas conectándose con Google Calendar mediante prompts y etapas configurables",
            activation_code="FLOW_RESERVA_INIT",
            tools=[
                {
                    "name": "get_available_slots",
                    "description": "Obtiene los horarios disponibles para una fecha específica",
                    "input": {"date_iso": "string (YYYY-MM-DD)"},
                    "output": {"slots": "array de {date_iso, start_time_iso, end_time_iso, available}"},
                },
                {
                    "name": "check_availability",
                    "description": "Verifica si un horario específico está disponible",
                    "input": {"date_iso": "string", "start_time_iso": "string", "end_time_iso": "string"},
                    "output": {"available": "boolean"},
                },
                {
                    "name": "create_booking",
                    "description": "Crea una nueva reserva",
                    "input": {"customer_id": "string", "customer_name": "string", "date_iso": "string", "start_time_iso": "string", "end_time_iso": "string"},
                    "output": {"success": "boolean", "booking_id": "string", "date_iso": "string", "start_time_iso": "string", "end_time_iso": "string"},
                },
                {
                    "name": "get_booking",
                    "description": "Obtiene los detalles de una reserva por ID",
                    "input": {"booking_id": "string"},
                    "output": {"found": "boolean", "booking_id": "string", "customer_id": "string", "date_iso": "string", "status": "string"},
                },
                {
                    "name": "list_bookings",
                    "description": "Lista todas las reservas de un cliente",
                    "input": {"customer_id": "string"},
                    "output": {"bookings": "array de reservas"},
                },
                {
                    "name": "update_booking",
                    "description": "Actualiza una reserva existente",
                    "input": {"booking_id": "string", "date_iso": "string (opcional)", "start_time_iso": "string (opcional)", "end_time_iso": "string (opcional)", "status": "string (opcional)"},
                    "output": {"success": "boolean", "booking_id": "string"},
                },
                {
                    "name": "delete_booking",
                    "description": "Elimina una reserva",
                    "input": {"booking_id": "string"},
                    "output": {"success": "boolean", "booking_id": "string"},
                },
            ],
            is_enabled=True,
        )
    
    # purchases
    if (automata_dir / "purchases").exists():
        registry["purchases"] = AutomatonMetadata(
            domain="purchases",
            display_name="Asistente de Compras",
            description="Autómata que gestiona consultas de órdenes, seguimiento de envíos y compras del cliente",
            activation_code="FLOW_COMPRA_INIT",
            tools=[
                {
                    "name": "get_order",
                    "description": "Obtiene los detalles de una orden por ID",
                    "input": {"order_id": "string (ORDER-XXX)"},
                    "output": {"found": "boolean", "order_id": "string", "customer_id": "string", "status": "string", "total_amount": "number"},
                },
                {
                    "name": "get_tracking_status",
                    "description": "Obtiene el estado de seguimiento de un envío",
                    "input": {"tracking_id": "string (TRACK-XXX)"},
                    "output": {"found": "boolean", "tracking_id": "string", "status": "string", "location": "string"},
                },
                {
                    "name": "list_orders",
                    "description": "Lista todas las órdenes de un cliente",
                    "input": {"customer_id": "string"},
                    "output": {"orders": "array de órdenes"},
                },
            ],
            is_enabled=True,
        )
    
    # claims
    if (automata_dir / "claims").exists():
        registry["claims"] = AutomatonMetadata(
            domain="claims",
            display_name="Asistente de Reclamos",
            description="Autómata que gestiona reclamos, quejas y devoluciones",
            activation_code="FLOW_RECLAMO_INIT",
            tools=[
                {
                    "name": "get_order",
                    "description": "Obtiene los detalles de una orden relacionada al reclamo",
                    "input": {"order_id": "string (ORDER-XXX)"},
                    "output": {"found": "boolean", "order_id": "string", "customer_id": "string", "status": "string"},
                },
            ],
            is_enabled=True,
        )
    
    # autonomous
    if (automata_dir / "autonomous").exists():
        registry["autonomous"] = AutomatonMetadata(
            domain="autonomous",
            display_name="Asistente Autónomo",
            description="Autómata autónomo con conversación natural para gestión de reservas con Google Calendar",
            activation_code="FLOW_AUTONOMO_INIT",
            tools=[
                {
                    "name": "get_available_slots",
                    "description": "Obtiene los horarios disponibles para una fecha específica",
                    "input": {"date_iso": "string (YYYY-MM-DD)"},
                    "output": {"slots": "array de {date_iso, start_time_iso, end_time_iso, available}"},
                },
                {
                    "name": "check_availability",
                    "description": "Verifica si un horario específico está disponible",
                    "input": {"date_iso": "string", "start_time_iso": "string", "end_time_iso": "string"},
                    "output": {"available": "boolean"},
                },
                {
                    "name": "create_booking",
                    "description": "Crea una nueva reserva",
                    "input": {"customer_id": "string", "customer_name": "string", "date_iso": "string", "start_time_iso": "string", "end_time_iso": "string"},
                    "output": {"success": "boolean", "booking_id": "string"},
                },
                {
                    "name": "get_booking",
                    "description": "Obtiene los detalles de una reserva por ID",
                    "input": {"booking_id": "string"},
                    "output": {"found": "boolean", "booking_id": "string", "customer_id": "string", "date_iso": "string", "status": "string"},
                },
                {
                    "name": "list_bookings",
                    "description": "Lista todas las reservas de un cliente",
                    "input": {"customer_id": "string"},
                    "output": {"bookings": "array de reservas"},
                },
                {
                    "name": "update_booking",
                    "description": "Actualiza una reserva existente",
                    "input": {"booking_id": "string", "date_iso": "string (opcional)", "start_time_iso": "string (opcional)", "end_time_iso": "string (opcional)", "status": "string (opcional)"},
                    "output": {"success": "boolean", "booking_id": "string"},
                },
                {
                    "name": "delete_booking",
                    "description": "Elimina una reserva",
                    "input": {"booking_id": "string"},
                    "output": {"success": "boolean", "booking_id": "string"},
                },
            ],
            is_enabled=True,
        )
    
    return registry


def get_domains_list() -> list[dict[str, Any]]:
    """Obtiene lista de dominios disponibles con su metadata."""
    registry = get_automata_registry()
    return [
        {
            "domain": meta.domain,
            "display_name": meta.display_name,
            "description": meta.description,
            "activation_code": meta.activation_code,
            "is_enabled": meta.is_enabled,
        }
        for meta in registry.values()
        if meta.is_enabled
    ]


def get_automaton_tools(domain: str) -> list[dict[str, Any]]:
    """Obtiene las herramientas disponibles para un dominio específico."""
    registry = get_automata_registry()
    if domain not in registry:
        return []
    return registry[domain].tools


def get_automaton_metadata(domain: str) -> AutomatonMetadata | None:
    """Obtiene metadata completa de un autómata por dominio."""
    registry = get_automata_registry()
    return registry.get(domain)
