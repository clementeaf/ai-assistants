from __future__ import annotations

import re
from collections.abc import Callable
from datetime import datetime
from typing import TypedDict

from langgraph.graph import END, StateGraph

from ai_assistants.agents.bookings_runtime import get_bookings_planner
from ai_assistants.agents.claims_runtime import get_claims_planner
from ai_assistants.agents.purchases_runtime import get_purchases_planner
from ai_assistants.orchestrator.state import ConversationState, MessageRole
from ai_assistants.tools.contracts import (
    CheckAvailabilityInput,
    CreateBookingInput,
    GetAvailableSlotsInput,
    GetOrderInput,
    GetTrackingInput,
    ListOrdersInput,
)
from ai_assistants.tools.bookings_tools import check_availability, create_booking, get_available_slots
from ai_assistants.tools.purchases_tools import get_order, get_tracking_status, list_orders
from ai_assistants.routing.domain_router import Domain, route_domain
from ai_assistants.memory.vector_runtime import get_vector_memory_tools
from ai_assistants.utils.time import utc_now

RouterFn = Callable[[str], Domain]


class GraphState(TypedDict):
    """LangGraph state container."""

    conversation: ConversationState
    user_text: str
    domain: Domain
    response_text: str


_ORDER_ID_PATTERN = re.compile(r"\b(ORDER-\d+)\b", flags=re.IGNORECASE)
_TRACKING_ID_PATTERN = re.compile(r"\b(TRACK-\d+)\b", flags=re.IGNORECASE)
_AMOUNT_PATTERN = re.compile(r"\b(\d+(?:[.,]\d+)?)\b")


def _infer_customer_id(conversation_id: str) -> str | None:
    """Infer customer id from conversation id for WhatsApp-style ids (e.g., whatsapp:+number)."""
    if ":" not in conversation_id:
        return None
    prefix, sender = conversation_id.split(":", 1)
    if prefix != "whatsapp":
        return None
    sender = sender.strip()
    return sender if sender != "" else None


def _make_route_node(router_fn: RouterFn) -> Callable[[GraphState], GraphState]:
    """Create a route node using the provided router function."""

    def _node(state: GraphState) -> GraphState:
        domain = router_fn(state["user_text"])
        conversation = state["conversation"].model_copy(update={"routed_domain": domain})
        return {**state, "domain": domain, "conversation": conversation}

    return _node


def purchases_node(state: GraphState) -> GraphState:
    """Handle purchase and tracking requests."""
    text = state["user_text"].lower()
    conversation_id = state["conversation"].conversation_id
    customer_id = state["conversation"].customer_id or _infer_customer_id(conversation_id)
    conversation = state["conversation"]

    wants_list = any(phrase in text for phrase in ("mis compras", "mis pedidos", "listar compras", "ver compras"))
    if wants_list:
        if customer_id is None:
            response = "¿Cuál es tu identificador de cliente para listar tus compras?"
            return {**state, "response_text": response}
        out = list_orders(ListOrdersInput(customer_id=customer_id))
        if out.error_code == "hook_unavailable":
            return {
                **state,
                "response_text": "En este momento no puedo consultar tus compras. Probá de nuevo en unos minutos.",
            }
        if len(out.orders) == 0:
            return {**state, "response_text": "No encontré compras asociadas a tu cuenta."}

        lines = ["Estas son tus compras recientes:"]
        for order in out.orders[:5]:
            tracking = f", tracking={order.tracking_id}" if order.tracking_id else ""
            lines.append(
                f"- {order.order_id}: estado={order.status}, total={order.total_amount} {order.currency}{tracking}"
            )
        return {**state, "response_text": "\n".join(lines), "conversation": conversation}

    tracking_match = _TRACKING_ID_PATTERN.search(state["user_text"])
    if tracking_match is not None:
        tracking_id = tracking_match.group(1).upper()
        conversation = conversation.model_copy(update={"last_tracking_id": tracking_id})
        tracking_out = get_tracking_status(GetTrackingInput(tracking_id=tracking_id))
        if tracking_out.error_code == "hook_unavailable":
            return {
                **state,
                "response_text": "En este momento no puedo consultar el seguimiento. Probá de nuevo en unos minutos.",
                "conversation": conversation,
            }
        if not tracking_out.found:
            return {**state, "response_text": f"No encontré el tracking {tracking_id}. Verificá el código.", "conversation": conversation}
        eta = f", ETA={tracking_out.estimated_delivery_iso}" if tracking_out.estimated_delivery_iso else ""
        response = (
            f"Tracking {tracking_out.tracking_id} ({tracking_out.carrier}): estado={tracking_out.status}, "
            f"última actualización={tracking_out.last_update_iso}{eta}."
        )
        if customer_id is not None:
            tools = get_vector_memory_tools()
            if tools is not None:
                tools.remember(customer_id=customer_id, text=response)
        return {**state, "response_text": response, "conversation": conversation}

    order_match = _ORDER_ID_PATTERN.search(state["user_text"])
    if order_match is None:
        # LLM planner (intelligence-first): propose validated tool calls for ambiguous messages.
        planner = get_purchases_planner()
        if planner is not None:
            plan = planner.plan(
                user_text=state["user_text"],
                customer_id=customer_id,
                last_order_id=conversation.last_order_id,
                last_tracking_id=conversation.last_tracking_id,
            )
            if plan is not None:
                for action in plan.actions:
                    if action.type == "ask_user":
                        return {**state, "response_text": action.text, "conversation": conversation}
                    # tool_call execution (allowlisted by schema)
                    if action.tool == "list_orders":
                        if customer_id is None:
                            return {
                                **state,
                                "response_text": "¿Cuál es tu identificador de cliente para listar tus compras?",
                                "conversation": conversation,
                            }
                        out = list_orders(ListOrdersInput(customer_id=customer_id))
                        if out.error_code == "hook_unavailable":
                            return {
                                **state,
                                "response_text": "En este momento no puedo consultar tus compras. Probá de nuevo en unos minutos.",
                                "conversation": conversation,
                            }
                        if len(out.orders) == 0:
                            return {**state, "response_text": "No encontré compras asociadas a tu cuenta.", "conversation": conversation}
                        lines = ["Estas son tus compras recientes:"]
                        for order in out.orders[:5]:
                            tracking = f", tracking={order.tracking_id}" if order.tracking_id else ""
                            lines.append(
                                f"- {order.order_id}: estado={order.status}, total={order.total_amount} {order.currency}{tracking}"
                            )
                        return {**state, "response_text": "\n".join(lines), "conversation": conversation}

                    if action.tool == "get_order":
                        order_id = action.args.get("order_id")
                        if not isinstance(order_id, str) or order_id.strip() == "":
                            continue
                        order_id = order_id.upper()
                        conversation = conversation.model_copy(update={"last_order_id": order_id})
                        order_out = get_order(GetOrderInput(order_id=order_id))
                        if order_out.error_code == "hook_unavailable":
                            return {
                                **state,
                                "response_text": "En este momento no puedo consultar la compra. Probá de nuevo en unos minutos.",
                                "conversation": conversation,
                            }
                        if not order_out.found:
                            return {
                                **state,
                                "response_text": f"No encontré la orden {order_id}. Verificá el código.",
                                "conversation": conversation,
                            }
                        base = (
                            f"Orden {order_out.order_id}: estado={order_out.status}, total={order_out.total_amount} "
                            f"{order_out.currency}, creada={order_out.created_at_iso}."
                        )
                        if order_out.tracking_id is None:
                            return {**state, "response_text": base, "conversation": conversation}
                        tracking_out = get_tracking_status(GetTrackingInput(tracking_id=order_out.tracking_id))
                        if tracking_out.error_code == "hook_unavailable":
                            return {
                                **state,
                                "response_text": "En este momento no puedo consultar el seguimiento. Probá de nuevo en unos minutos.",
                                "conversation": conversation,
                            }
                        if tracking_out.found:
                            eta = f", ETA={tracking_out.estimated_delivery_iso}" if tracking_out.estimated_delivery_iso else ""
                            response = (
                                f"{base}\nTracking {tracking_out.tracking_id} ({tracking_out.carrier}): estado={tracking_out.status}, "
                                f"última actualización={tracking_out.last_update_iso}{eta}."
                            )
                            return {**state, "response_text": response, "conversation": conversation}
                        return {
                            **state,
                            "response_text": f"{base}\nTracking: {order_out.tracking_id} (sin datos disponibles).",
                            "conversation": conversation,
                        }

                    if action.tool == "get_tracking_status":
                        tracking_id = action.args.get("tracking_id")
                        order_id = action.args.get("order_id")
                        if isinstance(tracking_id, str) and tracking_id.strip() != "":
                            tracking_id = tracking_id.upper()
                            conversation = conversation.model_copy(update={"last_tracking_id": tracking_id})
                            tracking_out = get_tracking_status(GetTrackingInput(tracking_id=tracking_id))
                        elif isinstance(order_id, str) and order_id.strip() != "":
                            order_id = order_id.upper()
                            conversation = conversation.model_copy(update={"last_order_id": order_id})
                            tracking_out = get_tracking_status(GetTrackingInput(order_id=order_id))
                        else:
                            continue
                        if tracking_out.error_code == "hook_unavailable":
                            return {
                                **state,
                                "response_text": "En este momento no puedo consultar el seguimiento. Probá de nuevo en unos minutos.",
                                "conversation": conversation,
                            }
                        if not tracking_out.found:
                            return {
                                **state,
                                "response_text": "No encontré el seguimiento. ¿Tenés un TRACK-XXX u ORDER-XXX?",
                                "conversation": conversation,
                            }
                        eta = f", ETA={tracking_out.estimated_delivery_iso}" if tracking_out.estimated_delivery_iso else ""
                        response = (
                            f"Tracking {tracking_out.tracking_id} ({tracking_out.carrier}): estado={tracking_out.status}, "
                            f"última actualización={tracking_out.last_update_iso}{eta}."
                        )
                        if customer_id is not None:
                            tools = get_vector_memory_tools()
                            if tools is not None:
                                tools.remember(customer_id=customer_id, text=response)
                        return {**state, "response_text": response, "conversation": conversation}

                    if action.tool == "vector_recall":
                        if customer_id is None:
                            continue
                        tools = get_vector_memory_tools()
                        if tools is None:
                            continue
                        query = action.args.get("query")
                        k = action.args.get("k", 3)
                        if not isinstance(query, str) or query.strip() == "":
                            query = state["user_text"]
                        if not isinstance(k, int):
                            k = 3
                        recalled = tools.recall(customer_id=customer_id, query=query, k=k)
                        for entry in recalled:
                            tm = _TRACKING_ID_PATTERN.search(entry.text)
                            if tm is not None:
                                tracking_id = tm.group(1).upper()
                                tracking_out = get_tracking_status(GetTrackingInput(tracking_id=tracking_id))
                                if tracking_out.found:
                                    eta = f", ETA={tracking_out.estimated_delivery_iso}" if tracking_out.estimated_delivery_iso else ""
                                    response = (
                                        f"Tracking {tracking_out.tracking_id} ({tracking_out.carrier}): estado={tracking_out.status}, "
                                        f"última actualización={tracking_out.last_update_iso}{eta}."
                                    )
                                    return {**state, "response_text": response, "conversation": conversation}
                            om = _ORDER_ID_PATTERN.search(entry.text)
                            if om is not None:
                                order_id = om.group(1).upper()
                                order_out = get_order(GetOrderInput(order_id=order_id))
                                if order_out.found:
                                    base = (
                                        f"Orden {order_out.order_id}: estado={order_out.status}, total={order_out.total_amount} "
                                        f"{order_out.currency}, creada={order_out.created_at_iso}."
                                    )
                                    return {**state, "response_text": base, "conversation": conversation}

        # Follow-up support: allow implicit tracking/order based on short-term memory.
        if any(word in text for word in ("seguimiento", "tracking", "envío", "envio")):
            remembered_tracking = conversation.last_tracking_id
            if remembered_tracking is None:
                remembered_tracking = conversation.customer_memory.get("last_tracking_id")
            if remembered_tracking is not None:
                tracking_out = get_tracking_status(GetTrackingInput(tracking_id=remembered_tracking))
                if tracking_out.error_code == "hook_unavailable":
                    return {
                        **state,
                        "response_text": "En este momento no puedo consultar el seguimiento. Probá de nuevo en unos minutos.",
                        "conversation": conversation,
                    }
                if tracking_out.found:
                    eta = f", ETA={tracking_out.estimated_delivery_iso}" if tracking_out.estimated_delivery_iso else ""
                    response = (
                        f"Tracking {tracking_out.tracking_id} ({tracking_out.carrier}): estado={tracking_out.status}, "
                        f"última actualización={tracking_out.last_update_iso}{eta}."
                    )
                    return {**state, "response_text": response, "conversation": conversation}

        remembered_order = conversation.last_order_id
        if remembered_order is None:
            remembered_order = conversation.customer_memory.get("last_order_id")
        if remembered_order is not None and any(word in text for word in ("orden", "pedido", "compra", "estado")):
            order_out = get_order(GetOrderInput(order_id=remembered_order))
            if order_out.error_code == "hook_unavailable":
                return {
                    **state,
                    "response_text": "En este momento no puedo consultar la compra. Probá de nuevo en unos minutos.",
                    "conversation": conversation,
                }
            if order_out.found:
                base = (
                    f"Orden {order_out.order_id}: estado={order_out.status}, total={order_out.total_amount} "
                    f"{order_out.currency}, creada={order_out.created_at_iso}."
                )
                return {**state, "response_text": base, "conversation": conversation}

        # Proactive check: "mes pasado" -> list orders and propose candidates.
        if customer_id is not None and any(phrase in text for phrase in ("mes pasado", "mes anterior")):
            out = list_orders(ListOrdersInput(customer_id=customer_id))
            if out.error_code == "hook_unavailable":
                return {
                    **state,
                    "response_text": "En este momento no puedo consultar tus compras. Probá de nuevo en unos minutos.",
                    "conversation": conversation,
                }
            now = utc_now()
            prev_year = now.year if now.month > 1 else now.year - 1
            prev_month = now.month - 1 if now.month > 1 else 12

            candidates = []
            for order in out.orders:
                try:
                    created = datetime.fromisoformat(order.created_at_iso)
                except ValueError:
                    continue
                if created.tzinfo is None:
                    continue
                if created.year == prev_year and created.month == prev_month:
                    candidates.append(order)

            if len(candidates) == 0:
                return {
                    **state,
                    "response_text": "No encontré compras del mes pasado. ¿Tenés el ID de la orden (ORDER-XXX) o tracking (TRACK-XXX)?",
                    "conversation": conversation,
                }
            # If the user provided an amount, try to disambiguate automatically.
            amount_match = _AMOUNT_PATTERN.search(text)
            if amount_match is not None:
                raw_amount = amount_match.group(1).replace(",", ".")
                try:
                    requested_amount = float(raw_amount)
                except ValueError:
                    requested_amount = None
                if requested_amount is not None:
                    for order in candidates:
                        if abs(order.total_amount - requested_amount) < 0.01:
                            # Resolve as if user gave the order id.
                            order_out = get_order(GetOrderInput(order_id=order.order_id))
                            if order_out.found:
                                base = (
                                    f"Orden {order_out.order_id}: estado={order_out.status}, total={order_out.total_amount} "
                                    f"{order_out.currency}, creada={order_out.created_at_iso}."
                                )
                                if order_out.tracking_id is None:
                                    return {**state, "response_text": base, "conversation": conversation}
                                tracking_out = get_tracking_status(GetTrackingInput(tracking_id=order_out.tracking_id))
                                if tracking_out.found:
                                    eta = (
                                        f", ETA={tracking_out.estimated_delivery_iso}"
                                        if tracking_out.estimated_delivery_iso
                                        else ""
                                    )
                                    response = (
                                        f"{base}\nTracking {tracking_out.tracking_id} ({tracking_out.carrier}): "
                                        f"estado={tracking_out.status}, última actualización={tracking_out.last_update_iso}{eta}."
                                    )
                                    return {**state, "response_text": response, "conversation": conversation}
                                return {
                                    **state,
                                    "response_text": f"{base}\nTracking: {order_out.tracking_id} (sin datos disponibles).",
                                    "conversation": conversation,
                                }

            lines = [
                "Encontré estas compras del mes pasado. ¿A cuál te referís?",
                "Si me decís el monto aproximado (por ejemplo: 120) puedo identificarla.",
            ]
            for order in candidates[:5]:
                tracking = f", tracking={order.tracking_id}" if order.tracking_id else ""
                lines.append(
                    f"- {order.order_id}: estado={order.status}, total={order.total_amount} {order.currency}{tracking}"
                )
            return {**state, "response_text": "\n".join(lines), "conversation": conversation}

        # Proactive vector recall: infer ORDER/TRACK from semantic memory snippets.
        if customer_id is not None:
            tools = get_vector_memory_tools()
            if tools is not None:
                recalled = tools.recall(customer_id=customer_id, query=state["user_text"], k=3)
                for entry in recalled:
                    tm = _TRACKING_ID_PATTERN.search(entry.text)
                    if tm is not None:
                        tracking_id = tm.group(1).upper()
                        tracking_out = get_tracking_status(GetTrackingInput(tracking_id=tracking_id))
                        if tracking_out.found:
                            eta = f", ETA={tracking_out.estimated_delivery_iso}" if tracking_out.estimated_delivery_iso else ""
                            response = (
                                f"Tracking {tracking_out.tracking_id} ({tracking_out.carrier}): estado={tracking_out.status}, "
                                f"última actualización={tracking_out.last_update_iso}{eta}."
                            )
                            return {**state, "response_text": response, "conversation": conversation}
                    om = _ORDER_ID_PATTERN.search(entry.text)
                    if om is not None:
                        order_id = om.group(1).upper()
                        order_out = get_order(GetOrderInput(order_id=order_id))
                        if order_out.found:
                            base = (
                                f"Orden {order_out.order_id}: estado={order_out.status}, total={order_out.total_amount} "
                                f"{order_out.currency}, creada={order_out.created_at_iso}."
                            )
                            return {**state, "response_text": base, "conversation": conversation}

        response = (
            "Decime el ID de la orden (por ejemplo: ORDER-100) o el tracking (por ejemplo: TRACK-9002). "
            "También podés pedir 'mis compras'."
        )
        return {**state, "response_text": response, "conversation": conversation}

    order_id = order_match.group(1).upper()
    conversation = conversation.model_copy(update={"last_order_id": order_id})
    order_out = get_order(GetOrderInput(order_id=order_id))
    if order_out.error_code == "hook_unavailable":
        return {
            **state,
            "response_text": "En este momento no puedo consultar la compra. Probá de nuevo en unos minutos.",
            "conversation": conversation,
        }
    if not order_out.found:
        response = f"No encontré la orden {order_id}. Verificá el identificador y probá de nuevo."
        return {**state, "response_text": response, "conversation": conversation}

    base = (
        f"Orden {order_out.order_id}: estado={order_out.status}, total={order_out.total_amount} "
        f"{order_out.currency}, creada={order_out.created_at_iso}."
    )
    if order_out.tracking_id is None:
        if customer_id is not None:
            tools = get_vector_memory_tools()
            if tools is not None:
                tools.remember(customer_id=customer_id, text=base)
        return {**state, "response_text": base, "conversation": conversation}

    conversation = conversation.model_copy(update={"last_tracking_id": order_out.tracking_id})
    tracking_out = get_tracking_status(GetTrackingInput(tracking_id=order_out.tracking_id))
    if tracking_out.error_code == "hook_unavailable":
        return {
            **state,
            "response_text": f"{base}\nEn este momento no puedo consultar el seguimiento. Probá de nuevo en unos minutos.",
            "conversation": conversation,
        }
    if not tracking_out.found:
        return {**state, "response_text": f"{base}\nTracking: {order_out.tracking_id} (sin datos disponibles).", "conversation": conversation}

    eta = f", ETA={tracking_out.estimated_delivery_iso}" if tracking_out.estimated_delivery_iso else ""
    response = (
        f"{base}\nTracking {tracking_out.tracking_id} ({tracking_out.carrier}): estado={tracking_out.status}, "
        f"última actualización={tracking_out.last_update_iso}{eta}."
    )
    if customer_id is not None:
        tools = get_vector_memory_tools()
        if tools is not None:
            tools.remember(customer_id=customer_id, text=response)
    return {**state, "response_text": response, "conversation": conversation}


def _is_first_interaction(conversation: ConversationState) -> bool:
    """Check if this is the first interaction (no assistant messages yet)."""
    return not any(msg.role == MessageRole.assistant for msg in conversation.messages)


def _extract_name_from_text(text: str) -> str | None:
    """Extract a name from user text (simple heuristic)."""
    text = text.strip()
    if len(text) < 2 or len(text) > 50:
        return None
    words = text.split()
    if len(words) == 1:
        return words[0].title()
    if len(words) <= 3:
        return " ".join(word.title() for word in words)
    return None


def _is_confirmation(text: str) -> bool:
    """Check if user text indicates confirmation."""
    text_lower = text.lower().strip()
    confirmations = ("sí", "si", "confirmo", "confirmar", "ok", "okay", "dale", "perfecto", "de acuerdo")
    return any(word in text_lower for word in confirmations)


def bookings_node(state: GraphState) -> GraphState:
    """Handle booking-related requests."""
    conversation_id = state["conversation"].conversation_id
    customer_id = state["conversation"].customer_id or _infer_customer_id(conversation_id)
    conversation = state["conversation"]
    user_text = state["user_text"].strip()

    # Step 1: Saludo inicial (máximo 2 líneas) si es la primera interacción
    if _is_first_interaction(conversation):
        greeting = "Hola, soy tu asistente de reservas.\n¿Cómo te llamás?"
        return {**state, "response_text": greeting, "conversation": conversation}

    # Step 2: Capturar nombre del usuario si no lo tenemos
    if conversation.customer_name is None:
        name = _extract_name_from_text(user_text)
        if name is not None:
            conversation = conversation.model_copy(update={"customer_name": name})
            response = f"Mucho gusto, {name}. ¿Qué fecha y horario te gustaría reservar?"
            return {**state, "response_text": response, "conversation": conversation}
        response = "Por favor, decime tu nombre para continuar con la reserva."
        return {**state, "response_text": response, "conversation": conversation}

    # Check if user is confirming a booking and we have all required data
    if (
        _is_confirmation(user_text)
        and conversation.requested_booking_date is not None
        and conversation.requested_booking_start_time is not None
        and conversation.requested_booking_end_time is not None
        and customer_id is not None
        and conversation.customer_name is not None
    ):
        booking_out = create_booking(
            CreateBookingInput(
                customer_id=customer_id,
                customer_name=conversation.customer_name,
                date_iso=conversation.requested_booking_date,
                start_time_iso=conversation.requested_booking_start_time,
                end_time_iso=conversation.requested_booking_end_time,
            )
        )
        if booking_out.success and booking_out.booking_id is not None:
            conversation = conversation.model_copy(update={"last_booking_id": booking_out.booking_id})
            start = conversation.requested_booking_start_time.split("T")[1].split(":")[:2]
            end = conversation.requested_booking_end_time.split("T")[1].split(":")[:2]
            response = (
                f"¡Reserva confirmada! Tu reserva {booking_out.booking_id} está confirmada para el "
                f"{conversation.requested_booking_date} de {':'.join(start)} a {':'.join(end)}.\n"
                f"Te enviaremos un email de confirmación y te avisaremos con anticipación como recordatorio."
            )
            if customer_id is not None:
                tools = get_vector_memory_tools()
                if tools is not None:
                    tools.remember(customer_id=customer_id, text=response)
            return {**state, "response_text": response, "conversation": conversation}

    # LLM planner (intelligence-first): propose validated tool calls for ambiguous messages.
    planner = get_bookings_planner()
    if planner is not None:
        plan = planner.plan(
            user_text=user_text,
            customer_id=customer_id,
        )
        if plan is not None:
            for action in plan.actions:
                if action.type == "ask_user":
                    return {**state, "response_text": action.text, "conversation": conversation}

                # Step 3: Consultar disponibilidad de calendario
                if action.tool == "get_available_slots":
                    date_iso = action.args.get("date_iso")
                    if not isinstance(date_iso, str) or date_iso.strip() == "":
                        return {
                            **state,
                            "response_text": "Necesito la fecha para consultar disponibilidad. ¿Qué fecha te interesa? (formato: YYYY-MM-DD)",
                            "conversation": conversation,
                        }
                    slots_out = get_available_slots(GetAvailableSlotsInput(date_iso=date_iso))
                    if slots_out.error_code is not None:
                        return {
                            **state,
                            "response_text": "No pude consultar la disponibilidad en este momento. Probá de nuevo en unos minutos.",
                            "conversation": conversation,
                        }
                    if len(slots_out.slots) == 0:
                        return {
                            **state,
                            "response_text": f"No hay horarios disponibles para el {date_iso}. ¿Querés consultar otra fecha?",
                            "conversation": conversation,
                        }
                    lines = [f"Horarios disponibles para el {date_iso}:"]
                    for slot in slots_out.slots[:10]:
                        start = slot.start_time_iso.split("T")[1].split(":")[:2]
                        end = slot.end_time_iso.split("T")[1].split(":")[:2]
                        lines.append(f"- {':'.join(start)} a {':'.join(end)}")
                    return {**state, "response_text": "\n".join(lines), "conversation": conversation}

                # Step 4: Validar disponibilidad para día/horario solicitado
                if action.tool == "check_availability":
                    date_iso = action.args.get("date_iso")
                    start_time_iso = action.args.get("start_time_iso")
                    end_time_iso = action.args.get("end_time_iso")
                    if (
                        not isinstance(date_iso, str)
                        or not isinstance(start_time_iso, str)
                        or not isinstance(end_time_iso, str)
                    ):
                        return {
                            **state,
                            "response_text": "Necesito la fecha y horario completo para verificar disponibilidad.",
                            "conversation": conversation,
                        }
                    availability_out = check_availability(
                        CheckAvailabilityInput(
                            date_iso=date_iso, start_time_iso=start_time_iso, end_time_iso=end_time_iso
                        )
                    )
                    if availability_out.error_code is not None:
                        return {
                            **state,
                            "response_text": "No pude verificar la disponibilidad en este momento. Probá de nuevo en unos minutos.",
                            "conversation": conversation,
                        }
                    conversation = conversation.model_copy(
                        update={
                            "requested_booking_date": date_iso,
                            "requested_booking_start_time": start_time_iso,
                            "requested_booking_end_time": end_time_iso,
                        }
                    )
                    if availability_out.available:
                        start = start_time_iso.split("T")[1].split(":")[:2]
                        end = end_time_iso.split("T")[1].split(":")[:2]
                        response = f"¡Perfecto! El horario del {date_iso} de {':'.join(start)} a {':'.join(end)} está disponible. ¿Confirmás la reserva?"
                        return {**state, "response_text": response, "conversation": conversation}
                    start = start_time_iso.split("T")[1].split(":")[:2]
                    end = end_time_iso.split("T")[1].split(":")[:2]
                    response = f"Lo siento, el horario del {date_iso} de {':'.join(start)} a {':'.join(end)} no está disponible. ¿Querés consultar otros horarios?"
                    return {**state, "response_text": response, "conversation": conversation}

                # Step 5: Confirmar reserva
                if action.tool == "create_booking":
                    if customer_id is None:
                        return {
                            **state,
                            "response_text": "Necesito tu identificador de cliente para crear la reserva.",
                            "conversation": conversation,
                        }
                    booking_date = action.args.get("date_iso") or conversation.requested_booking_date
                    booking_start = action.args.get("start_time_iso") or conversation.requested_booking_start_time
                    booking_end = action.args.get("end_time_iso") or conversation.requested_booking_end_time
                    customer_name = action.args.get("customer_name") or conversation.customer_name
                    if (
                        not isinstance(booking_date, str)
                        or not isinstance(booking_start, str)
                        or not isinstance(booking_end, str)
                        or not isinstance(customer_name, str)
                    ):
                        return {
                            **state,
                            "response_text": "Faltan datos para crear la reserva. Necesito fecha, horario de inicio y fin.",
                            "conversation": conversation,
                        }
                    booking_out = create_booking(
                        CreateBookingInput(
                            customer_id=customer_id,
                            customer_name=customer_name,
                            date_iso=booking_date,
                            start_time_iso=booking_start,
                            end_time_iso=booking_end,
                        )
                    )
                    if not booking_out.success or booking_out.booking_id is None:
                        return {
                            **state,
                            "response_text": "No pude crear la reserva en este momento. Probá de nuevo en unos minutos.",
                            "conversation": conversation,
                        }
                    conversation = conversation.model_copy(update={"last_booking_id": booking_out.booking_id})
                    start = booking_start.split("T")[1].split(":")[:2]
                    end = booking_end.split("T")[1].split(":")[:2]
                    response = (
                        f"¡Reserva confirmada! Tu reserva {booking_out.booking_id} está confirmada para el "
                        f"{booking_date} de {':'.join(start)} a {':'.join(end)}.\n"
                        f"Te enviaremos un email de confirmación y te avisaremos con anticipación como recordatorio."
                    )
                    if customer_id is not None:
                        tools = get_vector_memory_tools()
                        if tools is not None:
                            tools.remember(customer_id=customer_id, text=response)
                    return {**state, "response_text": response, "conversation": conversation}

                if action.tool == "vector_recall":
                    if customer_id is None:
                        return {
                            **state,
                            "response_text": "¿Cuál es tu identificador de cliente para buscar tus reservas?",
                            "conversation": conversation,
                        }
                    tools = get_vector_memory_tools()
                    if tools is not None:
                        query = action.args.get("query", user_text)
                        k = int(action.args.get("k", 3))
                        recalled = tools.recall(customer_id=customer_id, query=str(query), k=k)
                        if recalled:
                            lines = ["Encontré estas reservas relacionadas:"]
                            for entry in recalled[:3]:
                                lines.append(f"- {entry.text}")
                            return {**state, "response_text": "\n".join(lines), "conversation": conversation}
                        return {
                            **state,
                            "response_text": "No encontré reservas relacionadas. ¿Querés hacer una nueva reserva?",
                            "conversation": conversation,
                        }
                    return {
                        **state,
                        "response_text": "La búsqueda de reservas no está disponible en este momento.",
                        "conversation": conversation,
                    }

    # Fallback: simple response
    return {**state, "response_text": f"Hola {conversation.customer_name}, ¿qué fecha y horario te gustaría reservar?"}


def claims_node(state: GraphState) -> GraphState:
    """Handle claims-related requests."""
    conversation_id = state["conversation"].conversation_id
    customer_id = state["conversation"].customer_id or _infer_customer_id(conversation_id)
    conversation = state["conversation"]

    # Check for explicit ORDER-XXX first (deterministic)
    order_match = _ORDER_ID_PATTERN.search(state["user_text"])
    if order_match is not None:
        order_id = order_match.group(1).upper()
        order_out = get_order(GetOrderInput(order_id=order_id))
        if order_out.found:
            base = (
                f"Orden {order_out.order_id}: estado={order_out.status}, total={order_out.total_amount} "
                f"{order_out.currency}, creada={order_out.created_at_iso}."
            )
            return {
                **state,
                "response_text": f"{base}\nContame el problema con esta orden para iniciar el reclamo.",
                "conversation": conversation,
            }
        return {
            **state,
            "response_text": f"No encontré la orden {order_id}. Verificá el identificador y probá de nuevo.",
            "conversation": conversation,
        }

    # LLM planner (intelligence-first): propose validated tool calls for ambiguous messages.
    planner = get_claims_planner()
    if planner is not None:
        plan = planner.plan(
            user_text=state["user_text"],
            customer_id=customer_id,
        )
        if plan is not None:
            for action in plan.actions:
                if action.type == "ask_user":
                    return {**state, "response_text": action.text, "conversation": conversation}
                # tool_call execution (allowlisted by schema)
                if action.tool == "get_order":
                    order_id = str(action.args.get("order_id", ""))
                    if not order_id:
                        return {
                            **state,
                            "response_text": "Necesito el ID de la orden (ORDER-XXX) para continuar.",
                            "conversation": conversation,
                        }
                    order_out = get_order(GetOrderInput(order_id=order_id))
                    if order_out.found:
                        base = (
                            f"Orden {order_out.order_id}: estado={order_out.status}, total={order_out.total_amount} "
                            f"{order_out.currency}, creada={order_out.created_at_iso}."
                        )
                        return {
                            **state,
                            "response_text": f"{base}\nContame el problema con esta orden para iniciar el reclamo.",
                            "conversation": conversation,
                        }
                    return {
                        **state,
                        "response_text": f"No encontré la orden {order_id}. Verificá el identificador y probá de nuevo.",
                        "conversation": conversation,
                    }
                if action.tool == "vector_recall":
                    if customer_id is None:
                        return {
                            **state,
                            "response_text": "¿Cuál es tu identificador de cliente para buscar reclamos relacionados?",
                            "conversation": conversation,
                        }
                    tools = get_vector_memory_tools()
                    if tools is not None:
                        query = action.args.get("query", state["user_text"])
                        k = int(action.args.get("k", 3))
                        recalled = tools.recall(customer_id=customer_id, query=str(query), k=k)
                        if recalled:
                            lines = ["Encontré información relacionada:"]
                            for entry in recalled[:3]:
                                lines.append(f"- {entry.text}")
                            return {**state, "response_text": "\n".join(lines), "conversation": conversation}
                        return {
                            **state,
                            "response_text": "No encontré reclamos relacionados. ¿Querés iniciar uno nuevo?",
                            "conversation": conversation,
                        }
                    return {
                        **state,
                        "response_text": "La búsqueda de reclamos no está disponible en este momento.",
                        "conversation": conversation,
                    }

    # Fallback: simple response
    return {**state, "response_text": "Entiendo. Contame el problema y, si aplica, el ID de orden (ORDER-XXX)."}


def unknown_node(state: GraphState) -> GraphState:
    """Fallback handler when the domain cannot be determined."""
    return {
        **state,
        "response_text": "¿Querés hacer una reserva, revisar una compra, o iniciar un reclamo? Contame un poco más.",
    }


def build_router_graph(router_fn: RouterFn | None = None) -> StateGraph[GraphState]:
    """Build the top-level router graph that delegates to domain handlers."""
    router = router_fn or route_domain
    graph = StateGraph(GraphState)
    graph.add_node("route", _make_route_node(router))
    graph.add_node("purchases", purchases_node)
    graph.add_node("bookings", bookings_node)
    graph.add_node("claims", claims_node)
    graph.add_node("unknown", unknown_node)

    graph.set_entry_point("route")

    def _choose_next(state: GraphState) -> str:
        return state["domain"]

    graph.add_conditional_edges(
        "route",
        _choose_next,
        {
            "purchases": "purchases",
            "bookings": "bookings",
            "claims": "claims",
            "unknown": "unknown",
        },
    )
    graph.add_edge("purchases", END)
    graph.add_edge("bookings", END)
    graph.add_edge("claims", END)
    graph.add_edge("unknown", END)
    return graph


