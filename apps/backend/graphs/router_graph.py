from __future__ import annotations

import json
import os
import re
from collections.abc import Callable
from datetime import datetime
from typing import Any, TypedDict

import httpx
from langgraph.graph import END, StateGraph

from ai_assistants.automata.bookings.runtime import get_bookings_planner
from ai_assistants.automata.claims.runtime import get_claims_planner
from ai_assistants.automata.purchases.runtime import get_purchases_planner
from ai_assistants.automata.autonomous.runtime import get_autonomous_planner
from ai_assistants.orchestrator.state import ConversationState, MessageRole
from ai_assistants.tools.contracts import (
    CheckAvailabilityInput,
    CreateBookingInput,
    DeleteBookingInput,
    GetAvailableSlotsInput,
    GetBookingInput,
    GetOrderInput,
    GetTrackingInput,
    ListBookingsInput,
    ListOrdersInput,
    UpdateBookingInput,
)
from ai_assistants.tools.bookings_tools import (
    check_availability,
    create_booking,
    delete_booking,
    get_available_slots,
    get_booking,
    list_bookings,
    update_booking,
)
from ai_assistants.tools.purchases_tools import get_order, get_tracking_status, list_orders
from ai_assistants.routing.domain_router import Domain, route_domain
from ai_assistants.routing.autonomous_config import load_autonomous_config
from ai_assistants.memory.vector_runtime import get_vector_memory_tools
from ai_assistants.utils.time import utc_now
from ai_assistants.adapters.registry import get_booking_log_adapter
from ai_assistants.exceptions.adapter_exceptions import AdapterError, AdapterUnavailableError
from ai_assistants.observability.logging import get_logger
from ai_assistants.config.llm_config import load_llm_config
from ai_assistants.llm.openai_compatible import OpenAICompatibleConfig, OpenAICompatibleClient
from ai_assistants.utils.prompts import load_prompt_text

RouterFn = Callable[[str], Domain]


class GraphState(TypedDict, total=False):
    """LangGraph state container."""

    conversation: ConversationState
    user_text: str
    domain: Domain
    response_text: str
    interactive_type: str | None
    buttons: list[str] | None
    list_title: str | None
    list_items: list[str | dict] | None


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
        conversation = state["conversation"]
        user_text = state["user_text"]
        
        # 0. Si el modo autónomo está habilitado, SIEMPRE usar autonomous (prioridad máxima)
        autonomous_cfg = load_autonomous_config()
        if autonomous_cfg.enabled:
            logger = get_logger()
            logger.info("autonomous.routing", enabled=True, user_text=user_text[:50])
            # Limpiar routed_domain para forzar modo autónomo
            updated_conversation = conversation.model_copy(update={"routed_domain": None})
            return {**state, "domain": "autonomous", "conversation": updated_conversation}
        
        # 1. Detectar códigos de activación de flujo o menú (FLOW_RESERVA_INIT, MENU_INIT, etc)
        flow_name, flow_domain, is_menu = _detect_flow_activation_code(user_text)
        if is_menu:
            # Registrar acceso por link (menú)
            _register_link_access(conversation, user_text.strip().upper(), flow_domain="menú")
            
            # Activar menú directamente
            flows = _get_active_flows()
            menu_data = _show_menu(flows)
            # Guardar los flujos en memoria para poder mapear números después
            updated_memory = dict(conversation.customer_memory)
            updated_memory["menu_flows"] = json.dumps(flows)
            updated_conversation = conversation.model_copy(update={"customer_memory": updated_memory})
            return {
                **state,
                "domain": "unknown",
                "conversation": updated_conversation,
                "response_text": menu_data.get("text", ""),
                "interactive_type": menu_data.get("interactive_type"),
                "buttons": menu_data.get("buttons"),
                "list_title": menu_data.get("list_title"),
                "list_items": menu_data.get("list_items"),
            }
        if flow_domain:
            # Registrar acceso por link (flujo específico)
            _register_link_access(conversation, user_text.strip().upper(), flow_domain=flow_domain)
            
            # Marcar en memoria que se activó por código
            updated_memory = dict(conversation.customer_memory)
            updated_memory["flow_activated_by_code"] = "true"
            updated_memory["flow_activation_code"] = flow_name
            updated_conversation = conversation.model_copy(
                update={"routed_domain": flow_domain, "customer_memory": updated_memory}
            )
            return {**state, "domain": flow_domain, "conversation": updated_conversation}
        
        # 2. Detectar "menu" o "menú"
        text_lower = user_text.strip().lower()
        if text_lower == "menu" or text_lower == "menú":
            return {**state, "domain": "unknown"}
        
        # 3. Detectar si el usuario escribió un número después de ver el menú
        menu_flows_json = conversation.customer_memory.get("menu_flows")
        if menu_flows_json:
            try:
                flows = json.loads(menu_flows_json)
                mapped_domain = _map_number_to_domain(user_text, flows)
                if mapped_domain:
                    # Limpiar el menú de memoria y actualizar el dominio
                    updated_memory = dict(conversation.customer_memory)
                    updated_memory.pop("menu_flows", None)
                    updated_conversation = conversation.model_copy(
                        update={"routed_domain": mapped_domain, "customer_memory": updated_memory}
                    )
                    return {**state, "domain": mapped_domain, "conversation": updated_conversation}
            except (json.JSONDecodeError, KeyError):
                pass
        
        # Si ya hay un dominio activo y el usuario está en medio de un flujo, mantener el dominio
        # PERO: Si el modo autónomo está habilitado, siempre usar autonomous (ya se verificó arriba)
        if conversation.routed_domain == "bookings":
            # Si ya tiene nombre o fecha solicitada, mantener bookings
            if conversation.customer_name is not None or conversation.requested_booking_date is not None:
                domain = "bookings"
            else:
                # Si no hay contexto de bookings, intentar detectar de nuevo
                domain = router_fn(user_text)
        elif conversation.routed_domain == "purchases":
            # Si ya tiene order_id o tracking_id, mantener purchases
            if conversation.last_order_id is not None or conversation.last_tracking_id is not None:
                domain = "purchases"
            else:
                domain = router_fn(user_text)
        elif conversation.routed_domain == "claims":
            # Mantener claims si ya está en ese flujo
            domain = "claims"
        else:
            # Sin contexto previo, usar el router normal
            domain = router_fn(user_text)
        
        conversation = conversation.model_copy(update={"routed_domain": domain})
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
    if len(text) < 2 or len(text) > 100:
        return None
    
    # Palabras comunes que NO son nombres
    common_words = {"hola", "hi", "hello", "buenos", "dias", "días", "tardes", "noches", "gracias", "thanks", "ok", "okay", "si", "sí", "no", "quiero", "hacer", "una", "reserva"}
    text_lower = text.lower().strip()
    
    # Si el texto completo es solo una palabra común, no es un nombre
    if text_lower in common_words:
        return None
    
    # Patrones comunes para introducir nombre
    import re
    patterns = [
        r"(?:me\s+llamo|soy|mi\s+nombre\s+es|me\s+llaman)\s+([A-Za-zÁÉÍÓÚáéíóúÑñ]+(?:\s+[A-Za-zÁÉÍÓÚáéíóúÑñ]+){0,2})",
        r"^hola,?\s+me\s+llamo\s+([A-Za-zÁÉÍÓÚáéíóúÑñ]+(?:\s+[A-Za-zÁÉÍÓÚáéíóúÑñ]+){0,2})",
        r"^soy\s+([A-Za-zÁÉÍÓÚáéíóúÑñ]+(?:\s+[A-Za-zÁÉÍÓÚáéíóúÑñ]+){0,2})",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Filtrar palabras comunes
            name_words = name.lower().split()
            if any(word in common_words for word in name_words):
                continue
            if 2 <= len(name) <= 50:
                words = name.split()
                if 1 <= len(words) <= 3:
                    return " ".join(word.capitalize() for word in words)
    
    # Fallback: si el texto es corto y parece un nombre directo (pero no palabras comunes)
    words = text.split()
    if len(words) == 1 and 2 <= len(words[0]) <= 20:
        if words[0].lower() not in common_words:
            return words[0].capitalize()
    if 2 <= len(words) <= 3 and all(2 <= len(w) <= 20 for w in words):
        if not any(w.lower() in common_words for w in words):
            return " ".join(word.capitalize() for word in words)
    
    return None


def _parse_date_and_time(user_text: str) -> tuple[str | None, str | None, str | None]:
    """
    Parsea fecha y hora del texto del usuario.
    
    Soporta formatos:
    - Fecha: día/mes (15/01), día de mes (15 de enero)
    - Hora: 24 horas (18 horas, 19:00), AM/PM (2 PM, 10 AM), rangos (18-20 horas)
    
    Returns:
        tuple: (date_iso, start_time_iso, end_time_iso) o (None, None, None) si no se encuentra
    """
    import re
    from datetime import datetime
    
    current_year = datetime.now().year
    date_iso = None
    start_time_iso = None
    end_time_iso = None
    
    # Patrones de fecha: día/mes (15/01) o día de mes (15 de enero)
    date_patterns = [
        r"(\d{1,2})/(\d{1,2})",  # 15/01
        r"(?:para\s+el|el|día)\s+(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)",
        r"(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)",
    ]
    
    months = {
        "enero": "01", "febrero": "02", "marzo": "03", "abril": "04", "mayo": "05", "junio": "06",
        "julio": "07", "agosto": "08", "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12"
    }
    
    # Extraer fecha
    for pattern in date_patterns:
        match = re.search(pattern, user_text.lower())
        if match:
            if "/" in pattern:  # Formato día/mes
                day = match.group(1).zfill(2)
                month = match.group(2).zfill(2)
                if 1 <= int(month) <= 12 and 1 <= int(day) <= 31:
                    date_iso = f"{current_year}-{month}-{day}"
                    break
            else:  # Formato día de mes
                day = match.group(1).zfill(2)
                month_name = match.group(2).lower()
                if month_name in months:
                    date_iso = f"{current_year}-{months[month_name]}-{day}"
                    break
    
    # Extraer hora (solo si ya tenemos fecha)
    if date_iso:
        # IMPORTANTE: Orden de patrones es crítico - más específicos primero
        # Patrones: 18 horas, 19:00, 2 PM, 10 AM, 9:30 AM, 18-20 horas
        time_patterns = [
            (r"(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)", "ampm_with_minutes"),  # 9:30 AM, 2:15 PM (MÁS ESPECÍFICO - PRIMERO)
            (r"(\d{1,2})\s*-\s*(\d{1,2})\s*(?:horas|hs|h)", "range_hours"),  # Rango: 18-20 horas
            (r"(\d{1,2}):(\d{2})(?:\s*-\s*(\d{1,2}):(\d{2}))?", "time_with_minutes"),  # 18:00 o 18:00-20:00
            (r"(\d{1,2})\s*(?:horas|hs|h)", "single_hour"),  # 18 horas
            (r"(\d{1,2})\s*(AM|PM|am|pm)", "ampm"),  # 2 PM, 10 AM
        ]
        
        for pattern, pattern_type in time_patterns:
            match = re.search(pattern, user_text, re.IGNORECASE)
            if match:
                if pattern_type == "ampm_with_minutes":  # Formato 9:30 AM
                    hour = int(match.group(1))
                    minute = int(match.group(2))
                    period = match.group(3).upper()
                    if period == "PM" and hour != 12:
                        hour += 12
                    elif period == "AM" and hour == 12:
                        hour = 0
                    # Usar zona horaria de Chile (UTC-3)
                    start_time_iso = f"{date_iso}T{hour:02d}:{minute:02d}:00-03:00"
                    # Calcular hora de fin (1 hora después por defecto)
                    end_hour = hour + 1
                    if end_hour >= 24:
                        end_hour = 0
                    end_time_iso = f"{date_iso}T{end_hour:02d}:{minute:02d}:00-03:00"
                elif pattern_type == "ampm":  # Formato AM/PM sin minutos
                    hour = int(match.group(1))
                    period = match.group(2).upper()
                    if period == "PM" and hour != 12:
                        hour += 12
                    elif period == "AM" and hour == 12:
                        hour = 0
                    # Usar zona horaria de Chile (UTC-3)
                    start_time_iso = f"{date_iso}T{hour:02d}:00:00-03:00"
                elif pattern_type == "time_with_minutes":  # Formato 18:00
                    hour = int(match.group(1))
                    minute = int(match.group(2))
                    # Usar zona horaria de Chile (UTC-3)
                    start_time_iso = f"{date_iso}T{hour:02d}:{minute:02d}:00-03:00"
                    # Rango si existe (grupos 3 y 4)
                    if match.lastindex and match.lastindex >= 4 and match.group(3) and match.group(4):
                        end_hour = int(match.group(3))
                        end_minute = int(match.group(4))
                        end_time_iso = f"{date_iso}T{end_hour:02d}:{end_minute:02d}:00-03:00"
                elif pattern_type == "range_hours":  # Rango: 18-20 horas
                    start_hour = int(match.group(1))
                    end_hour = int(match.group(2))
                    # Usar zona horaria de Chile (UTC-3)
                    start_time_iso = f"{date_iso}T{start_hour:02d}:00:00-03:00"
                    end_time_iso = f"{date_iso}T{end_hour:02d}:00:00-03:00"
                else:  # Formato 18 horas (single)
                    start_hour = int(match.group(1))
                    # Usar zona horaria de Chile (UTC-3)
                    start_time_iso = f"{date_iso}T{start_hour:02d}:00:00-03:00"
                break
    
    return (date_iso, start_time_iso, end_time_iso)


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

    # Detectar si fue activado por código de flujo (FLOW_RESERVA_INIT, etc)
    flow_activated = conversation.customer_memory.get("flow_activated_by_code") == "true"
    if flow_activated:
        # Limpiar el flag de activación
        updated_memory = dict(conversation.customer_memory)
        updated_memory.pop("flow_activated_by_code", None)
        updated_memory.pop("flow_activation_code", None)
        updated_conversation = conversation.model_copy(update={"customer_memory": updated_memory})
        
        # Enviar saludo inicial del flujo
        customer_name = conversation.customer_name
        if customer_name:
            greeting = f"¡Hola {customer_name}! Bienvenido al sistema de reservas.\n¿Qué fecha y horario te gustaría reservar?"
        else:
            greeting = "¡Hola! Bienvenido al sistema de reservas.\n¿Cómo te llamás?"
        return {**state, "response_text": greeting, "conversation": updated_conversation}

    # Step 1: Saludo inicial (máximo 2 líneas) si es la primera interacción
    if _is_first_interaction(conversation):
        # Consultar módulos del flujo activo para obtener el saludo configurado
        greeting_text = _get_greeting_from_flow()
        
        # Personalizar saludo con nombre si está disponible
        if conversation.customer_name:
            # Reemplazar "¿Cómo te llamas?" o similar si está en el texto
            greeting = greeting_text.replace("¿Cómo te llamas?", "").replace("¿Cómo te llamás?", "").strip()
            if not greeting.endswith(".") and not greeting.endswith("!"):
                greeting += "."
            greeting = f"¡Hola {conversation.customer_name}! {greeting}"
        else:
            greeting = greeting_text
        return {**state, "response_text": greeting, "conversation": conversation}

    # Step 2: Capturar nombre del usuario si no lo tenemos
    # IMPORTANTE: Solo ejecutar este paso si hay un módulo get_name configurado en el flujo
    # y si realmente no tenemos el nombre
    if conversation.customer_name is None:
        # Obtener el módulo get_name del flujo activo (si existe)
        get_name_stage = _get_name_stage_from_flow()
        
        # Si hay módulo get_name configurado, usar su prompt_text
        if get_name_stage:
            prompt_text = get_name_stage.get("prompt_text", "Por favor, dime tu nombre completo.")
            # Verificar si el usuario está mencionando "reserva" o similar (no es un nombre)
            text_lower = user_text.lower()
            if any(word in text_lower for word in ("reserva", "reservas", "turno", "agenda", "quiero", "necesito", "deseo")):
                # El usuario está expresando intención de reservar, no dando su nombre
                return {**state, "response_text": prompt_text, "conversation": conversation}
            
            name = _extract_name_from_text(user_text)
            if name is not None:
                conversation = conversation.model_copy(update={"customer_name": name})
                response = f"Mucho gusto, {name}. ¿Qué fecha y horario te gustaría reservar?"
                return {**state, "response_text": response, "conversation": conversation}
            return {**state, "response_text": prompt_text, "conversation": conversation}
        
        # Lógica por defecto si no hay módulo configurado
        # Verificar si el usuario está mencionando "reserva" o similar (no es un nombre)
        text_lower = user_text.lower()
        if any(word in text_lower for word in ("reserva", "reservas", "turno", "agenda", "quiero", "necesito", "deseo")):
            # El usuario está expresando intención de reservar, no dando su nombre
            response = "Perfecto, te ayudo con tu reserva. ¿Cómo te llamás?"
            return {**state, "response_text": response, "conversation": conversation}
        
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
            customer_name=conversation.customer_name,
            requested_booking_date=conversation.requested_booking_date,
            requested_booking_start_time=conversation.requested_booking_start_time,
            requested_booking_end_time=conversation.requested_booking_end_time,
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
                    slots_out = get_available_slots(GetAvailableSlotsInput(date_iso=date_iso, customer_id=customer_id))
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
                            date_iso=date_iso, start_time_iso=start_time_iso, end_time_iso=end_time_iso, customer_id=customer_id
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

                # Obtener reserva por ID
                if action.tool == "get_booking":
                    booking_id = action.args.get("booking_id")
                    if not isinstance(booking_id, str) or booking_id.strip() == "":
                        return {
                            **state,
                            "response_text": "Necesito el ID de la reserva para consultarla. ¿Cuál es el ID de tu reserva?",
                            "conversation": conversation,
                        }
                    booking_out = get_booking(GetBookingInput(booking_id=booking_id))
                    if not booking_out.found:
                        return {
                            **state,
                            "response_text": f"No encontré la reserva {booking_id}. Verificá el ID e intentá de nuevo.",
                            "conversation": conversation,
                        }
                    start = booking_out.start_time_iso.split("T")[1].split(":")[:2] if booking_out.start_time_iso else ["", ""]
                    end = booking_out.end_time_iso.split("T")[1].split(":")[:2] if booking_out.end_time_iso else ["", ""]
                    response = (
                        f"Reserva {booking_out.booking_id}:\n"
                        f"- Cliente: {booking_out.customer_name}\n"
                        f"- Fecha: {booking_out.date_iso}\n"
                        f"- Horario: {':'.join(start)} a {':'.join(end)}\n"
                        f"- Estado: {booking_out.status}"
                    )
                    return {**state, "response_text": response, "conversation": conversation}

                # Listar reservas del cliente
                if action.tool == "list_bookings":
                    if customer_id is None:
                        return {
                            **state,
                            "response_text": "Necesito tu identificador de cliente para listar tus reservas.",
                            "conversation": conversation,
                        }
                    bookings_out = list_bookings(ListBookingsInput(customer_id=customer_id))
                    if bookings_out.error_code is not None:
                        return {
                            **state,
                            "response_text": "No pude consultar tus reservas en este momento. Probá de nuevo en unos minutos.",
                            "conversation": conversation,
                        }
                    if len(bookings_out.bookings) == 0:
                        return {
                            **state,
                            "response_text": "No tenés reservas registradas. ¿Querés hacer una nueva reserva?",
                            "conversation": conversation,
                        }
                    lines = ["Tus reservas:"]
                    for booking in bookings_out.bookings[:10]:
                        start = booking.start_time_iso.split("T")[1].split(":")[:2]
                        end = booking.end_time_iso.split("T")[1].split(":")[:2]
                        lines.append(
                            f"- {booking.booking_id}: {booking.date_iso} de {':'.join(start)} a {':'.join(end)} ({booking.status})"
                        )
                    return {**state, "response_text": "\n".join(lines), "conversation": conversation}

                # Modificar reserva
                if action.tool == "update_booking":
                    booking_id = action.args.get("booking_id")
                    if not isinstance(booking_id, str) or booking_id.strip() == "":
                        return {
                            **state,
                            "response_text": "Necesito el ID de la reserva para modificarla. ¿Cuál es el ID de tu reserva?",
                            "conversation": conversation,
                        }
                    update_out = update_booking(
                        UpdateBookingInput(
                            booking_id=booking_id,
                            date_iso=action.args.get("date_iso"),
                            start_time_iso=action.args.get("start_time_iso"),
                            end_time_iso=action.args.get("end_time_iso"),
                            status=action.args.get("status"),
                        )
                    )
                    if not update_out.success:
                        if update_out.error_code == "booking_not_found":
                            return {
                                **state,
                                "response_text": f"No encontré la reserva {booking_id}. Verificá el ID e intentá de nuevo.",
                                "conversation": conversation,
                            }
                        return {
                            **state,
                            "response_text": "No pude modificar la reserva en este momento. Probá de nuevo en unos minutos.",
                            "conversation": conversation,
                        }
                    start = update_out.start_time_iso.split("T")[1].split(":")[:2] if update_out.start_time_iso else ["", ""]
                    end = update_out.end_time_iso.split("T")[1].split(":")[:2] if update_out.end_time_iso else ["", ""]
                    response = (
                        f"¡Reserva {update_out.booking_id} actualizada!\n"
                        f"- Fecha: {update_out.date_iso}\n"
                        f"- Horario: {':'.join(start)} a {':'.join(end)}\n"
                        f"- Estado: {update_out.status}"
                    )
                    if customer_id is not None:
                        tools = get_vector_memory_tools()
                        if tools is not None:
                            tools.remember(customer_id=customer_id, text=response)
                    return {**state, "response_text": response, "conversation": conversation}

                # Eliminar reserva
                if action.tool == "delete_booking":
                    booking_id = action.args.get("booking_id")
                    if not isinstance(booking_id, str) or booking_id.strip() == "":
                        return {
                            **state,
                            "response_text": "Necesito el ID de la reserva para eliminarla. ¿Cuál es el ID de tu reserva?",
                            "conversation": conversation,
                        }
                    delete_out = delete_booking(DeleteBookingInput(booking_id=booking_id))
                    if not delete_out.success:
                        if delete_out.error_code == "booking_not_found":
                            return {
                                **state,
                                "response_text": f"No encontré la reserva {booking_id}. Verificá el ID e intentá de nuevo.",
                                "conversation": conversation,
                            }
                        return {
                            **state,
                            "response_text": "No pude eliminar la reserva en este momento. Probá de nuevo en unos minutos.",
                            "conversation": conversation,
                        }
                    response = f"Reserva {delete_out.booking_id} eliminada correctamente."
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


def _get_active_flows() -> list[dict[str, Any]]:
    """Obtiene los flujos activos desde el servidor MCP de flujos."""
    from ai_assistants.config.mcp_config import load_mcp_config
    
    mcp_config = load_mcp_config()
    flow_server_url = mcp_config.booking_flow_server_url
    try:
        client = httpx.Client(timeout=5.0)
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "list_flows",
                "arguments": {"include_inactive": False},
            },
        }
        response = client.post(f"{flow_server_url}/mcp", json=payload)
        response.raise_for_status()
        json_response = response.json()
        if "error" in json_response and json_response["error"] is not None:
            return []
        result = json_response.get("result", {})
        flows = result.get("flows", [])
        return flows
    except (httpx.HTTPError, httpx.TimeoutException, httpx.RequestError) as exc:
        logger = get_logger()
        logger.warning("Failed to fetch active flows", error=str(exc))
        return []
    except Exception as exc:
        logger = get_logger()
        logger.error("Unexpected error fetching active flows", error=str(exc), error_type=type(exc).__name__)
        return []


def _get_greeting_from_flow() -> str:
    """
    Obtiene el texto del saludo desde el flujo activo configurado.
    @returns Texto del saludo o texto por defecto si no se encuentra
    """
    flows = _get_active_flows()
    booking_flow = next((f for f in flows if f.get("domain") == "bookings" and f.get("is_active")), None)
    
    if not booking_flow:
        return "Hola, soy tu asistente de reservas.\n¿Cómo te llamás?"
    
    try:
        flow_id = booking_flow.get("flow_id")
        if not flow_id:
            return "Hola, soy tu asistente de reservas.\n¿Cómo te llamás?"
        
        from ai_assistants.config.mcp_config import load_mcp_config
        
        mcp_config = load_mcp_config()
        flow_server_url = mcp_config.booking_flow_server_url
        client = httpx.Client(timeout=5.0)
        stages_response = client.post(
            f"{flow_server_url}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "get_flow_stages", "arguments": {"flow_id": flow_id}},
            },
        )
        if stages_response.status_code == 200:
            json_response = stages_response.json()
            if "error" not in json_response or json_response["error"] is None:
                result = json_response.get("result", {})
                stages = result.get("stages", [])
                greeting_stage = next((s for s in stages if s.get("stage_type") == "greeting"), None)
                if greeting_stage and greeting_stage.get("prompt_text"):
                    return greeting_stage.get("prompt_text")
    except (httpx.HTTPError, httpx.TimeoutException, httpx.RequestError) as exc:
        logger = get_logger()
        logger.warning("Failed to fetch greeting from flow", error=str(exc))
    except Exception as exc:
        logger = get_logger()
        logger.error("Unexpected error fetching greeting", error=str(exc), error_type=type(exc).__name__)
    
    return "Hola, soy tu asistente de reservas.\n¿Cómo te llamás?"


def _get_name_stage_from_flow() -> dict[str, Any] | None:
    """
    Obtiene el módulo get_name (input con field_name=customer_name) del flujo activo.
    @returns Diccionario con la información del stage o None si no existe
    """
    flows = _get_active_flows()
    booking_flow = next((f for f in flows if f.get("domain") == "bookings" and f.get("is_active")), None)
    
    if not booking_flow:
        return None
    
    try:
        flow_id = booking_flow.get("flow_id")
        if not flow_id:
            return None
        
        from ai_assistants.config.mcp_config import load_mcp_config
        
        mcp_config = load_mcp_config()
        flow_server_url = mcp_config.booking_flow_server_url
        client = httpx.Client(timeout=5.0)
        stages_response = client.post(
            f"{flow_server_url}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "get_flow_stages", "arguments": {"flow_id": flow_id}},
            },
        )
        if stages_response.status_code == 200:
            json_response = stages_response.json()
            if "error" not in json_response or json_response["error"] is None:
                result = json_response.get("result", {})
                stages = result.get("stages", [])
                get_name_stage = next(
                    (s for s in stages if s.get("stage_type") == "input" and s.get("field_name") == "customer_name"),
                    None
                )
                return get_name_stage
    except (httpx.HTTPError, httpx.TimeoutException, httpx.RequestError) as exc:
        logger = get_logger()
        logger.warning("Failed to fetch name stage from flow", error=str(exc))
    except Exception as exc:
        logger = get_logger()
        logger.error("Unexpected error fetching name stage", error=str(exc), error_type=type(exc).__name__)
    
    return None


def _register_link_access(
    conversation: ConversationState,
    activation_code: str,
    flow_domain: str | None = None,
) -> None:
    """
    Registra automáticamente el acceso por link en el booking log.
    @param conversation - Estado de la conversación con customer_id y customer_name
    @param activation_code - Código de activación usado (ej: FLOW_RESERVA_INIT)
    @param flow_domain - Dominio del flujo activado (opcional)
    """
    logger = get_logger()
    
    try:
        adapter = get_booking_log_adapter()
    except RuntimeError:
        logger.debug("Booking log adapter no configurado, omitiendo registro")
        return
    except AdapterUnavailableError as e:
        logger.warning("Booking log adapter unavailable", error=str(e), adapter_name=e.adapter_name)
        return
    except AdapterError as e:
        logger.warning("Error obteniendo booking log adapter", error=str(e))
        return
    
    # Obtener datos del cliente
    customer_id = conversation.customer_id or _infer_customer_id(conversation.conversation_id)
    customer_name = conversation.customer_name or "Cliente"
    
    # Si no hay customer_id, no podemos registrar
    if not customer_id:
        logger.debug("No se puede registrar acceso: customer_id no disponible")
        return
    
    # Obtener fecha y hora actual
    now = utc_now()
    date_iso = now.strftime("%Y-%m-%d")
    time_iso = now.isoformat()
    
    # Generar booking_code único: código_activación + timestamp + últimos 4 dígitos del customer_id
    import time
    timestamp_suffix = str(int(time.time()))[-6:]  # Últimos 6 dígitos del timestamp
    customer_suffix = customer_id[-4:] if len(customer_id) >= 4 else customer_id  # Últimos 4 dígitos del customer_id
    booking_code = f"{activation_code.upper()}-{timestamp_suffix}-{customer_suffix}"
    
    try:
        adapter.create_booking_log(
            booking_code=booking_code,
            customer_name=customer_name,
            customer_id=customer_id,
            date_iso=date_iso,
            time_iso=time_iso,
            observations=f"Acceso por link - Flujo: {flow_domain or 'menú'}",
        )
        logger.info(
            "Registro de acceso por link creado",
            booking_code=booking_code,
            customer_id=customer_id,
            customer_name=customer_name,
        )
    except AdapterUnavailableError as e:
        logger.warning(
            "Error registrando acceso por link: adapter unavailable",
            error=str(e),
            adapter_name=e.adapter_name,
            booking_code=booking_code,
            customer_id=customer_id,
        )
    except AdapterError as e:
        logger.warning(
            "Error registrando acceso por link en booking log",
            error=str(e),
            booking_code=booking_code,
            customer_id=customer_id,
        )


def _detect_flow_activation_code(user_text: str) -> tuple[str | None, str | None, bool]:
    """
    Detecta si el mensaje contiene un código de activación de flujo o menú.
    Retorna: (flow_name, domain, is_menu) 
    - Si detecta código de menú: (None, None, True)
    - Si detecta código de flujo: (flow_name, domain, False)
    - Si no detecta nada: (None, None, False)
    
    Formatos soportados:
    - FLOW_<NOMBRE>_INIT (ej: FLOW_RESERVA_INIT)
    - START_<NOMBRE> (ej: START_RESERVA)
    - MENU_INIT, FLOW_MENU_INIT (para mostrar menú)
    """
    text = user_text.strip().upper()
    
    # Detectar código de menú
    if text in ("MENU_INIT", "FLOW_MENU_INIT", "START_MENU"):
        return (None, None, True)
    
    # Formato FLOW_<NOMBRE>_INIT
    if text.startswith("FLOW_") and text.endswith("_INIT"):
        flow_name = text.replace("FLOW_", "").replace("_INIT", "")
        # Mapear nombres comunes a dominios
        domain_map = {
            "RESERVA": "bookings",
            "RESERVAS": "bookings",
            "BOOKING": "bookings",
            "COMPRA": "purchases",
            "COMPRAS": "purchases",
            "PURCHASE": "purchases",
            "RECLAMO": "claims",
            "RECLAMOS": "claims",
            "CLAIM": "claims",
        }
        domain = domain_map.get(flow_name)
        if domain:
            return (flow_name.lower(), domain, False)
    
    # Formato START_<NOMBRE>
    if text.startswith("START_"):
        flow_name = text.replace("START_", "")
        domain_map = {
            "RESERVA": "bookings",
            "RESERVAS": "bookings",
            "BOOKING": "bookings",
            "COMPRA": "purchases",
            "COMPRAS": "purchases",
            "PURCHASE": "purchases",
            "RECLAMO": "claims",
            "RECLAMOS": "claims",
            "CLAIM": "claims",
        }
        domain = domain_map.get(flow_name)
        if domain:
            return (flow_name.lower(), domain, False)
    
    return (None, None, False)


def _show_menu(flows: list[dict[str, Any]], use_interactive: bool = True) -> dict[str, Any]:
    """
    Genera el menú basado en los flujos activos.
    Retorna dict con 'text' y opcionalmente 'interactive_type', 'buttons', 'list_items'
    """
    if not flows:
        return {
            "text": "¿Querés hacer una reserva, revisar una compra, o iniciar un reclamo? Contame un poco más.",
        }
    
    # Si hay 3 o menos flujos, usar botones interactivos
    if use_interactive and len(flows) <= 3:
        buttons = []
        for flow in flows:
            name = flow.get("name", "Sin nombre")
            buttons.append(name)
        
        return {
            "text": "*Menú de opciones:*\n\nSelecciona una opción:",
            "interactive_type": "buttons",
            "buttons": buttons,
        }
    
    # Si hay más de 3 flujos, usar lista interactiva
    if use_interactive and len(flows) <= 10:
        list_items = []
        for flow in flows:
            name = flow.get("name", "Sin nombre")
            description = flow.get("description", "")
            if description:
                list_items.append({"title": name, "description": description})
            else:
                list_items.append(name)
        
        return {
            "text": "*Menú de opciones:*",
            "interactive_type": "list",
            "list_title": "Selecciona un flujo",
            "list_items": list_items,
        }
    
    # Fallback a texto simple si hay más de 10 flujos
    lines = ["*Menú de opciones:*\n"]
    for idx, flow in enumerate(flows, start=1):
        name = flow.get("name", "Sin nombre")
        description = flow.get("description", "")
        if description:
            lines.append(f"{idx}. {name} - {description}")
        else:
            lines.append(f"{idx}. {name}")
    
    lines.append("\nEscribe el *número* de la opción que deseas (ej: 1, 2, 3)")
    return {
        "text": "\n".join(lines),
    }


def _map_number_to_domain(user_text: str, flows: list[dict[str, Any]]) -> Domain | None:
    """Mapea un número ingresado por el usuario al dominio del flujo correspondiente."""
    text = user_text.strip()
    try:
        number = int(text)
        if 1 <= number <= len(flows):
            flow = flows[number - 1]
            domain = flow.get("domain", "bookings")
            if domain in ("bookings", "purchases", "claims"):
                return domain
    except ValueError:
        pass
    return None


def autonomous_node(state: GraphState) -> GraphState:
    """Autonomous LLM-powered node using planner pattern with tool execution."""
    logger = get_logger()
    conversation_id = state["conversation"].conversation_id
    customer_id = state["conversation"].customer_id or _infer_customer_id(conversation_id)
    conversation = state["conversation"]
    user_text = state["user_text"].strip()
    cfg = load_autonomous_config()

    if not cfg.enabled:
        logger.warning("autonomous.disabled")
        return unknown_node(state)

    planner = get_autonomous_planner()
    if planner is None:
        logger.warning("autonomous.planner.not_available")
        return unknown_node(state)

    # Step 0: RECUERDO - Verificar si es cliente recurrente (nueva conversación pero customer_id conocido)
    is_first = _is_first_interaction(conversation)
    is_recurring_customer = False
    previous_bookings_count = 0
    previous_bookings_summary = ""
    
    # Si es primera interacción Y tenemos customer_id, verificar si es cliente recurrente
    if is_first and customer_id:
        # 1. Verificar si hay nombre en customer_memory (memoria a largo plazo)
        memory_name = conversation.customer_memory.get("customer_name")
        if memory_name and not conversation.customer_name:
            conversation = conversation.model_copy(update={"customer_name": memory_name})
            logger.info("autonomous.memory.name_loaded", name=memory_name)
            is_recurring_customer = True
        
        # 2. Verificar reservas previas en la bitácora
        try:
            bookings_result = list_bookings(ListBookingsInput(customer_id=customer_id))
            if bookings_result.error_code is None and bookings_result.bookings:
                previous_bookings_count = len(bookings_result.bookings)
                # Obtener nombre de la primera reserva si no lo tenemos
                if not conversation.customer_name and bookings_result.bookings[0].customer_name:
                    conversation = conversation.model_copy(update={"customer_name": bookings_result.bookings[0].customer_name})
                    logger.info("autonomous.memory.name_from_booking", name=bookings_result.bookings[0].customer_name)
                
                # Crear resumen de reservas previas (últimas 3)
                recent_bookings = bookings_result.bookings[:3]
                booking_lines = []
                for booking in recent_bookings:
                    date_str = booking.date_iso
                    time_str = booking.start_time_iso.split("T")[1].split(":")[0:2] if "T" in booking.start_time_iso else ""
                    status_str = booking.status
                    booking_lines.append(f"- {date_str} a las {':'.join(time_str)} ({status_str})")
                
                if booking_lines:
                    previous_bookings_summary = "\n".join(booking_lines)
                    is_recurring_customer = True
                    logger.info("autonomous.memory.previous_bookings_found", count=previous_bookings_count)
        except Exception as e:
            logger.warning("autonomous.memory.booking_check_failed", error=str(e))
    
    logger.info("autonomous.first_interaction", is_first=is_first, is_recurring=is_recurring_customer, 
                has_name=bool(conversation.customer_name), previous_bookings=previous_bookings_count)
    
    # Step 1: Verificar si es primera interacción
    if is_first:
        # Intentar extraer nombre del mensaje antes de mostrar saludo
        name = _extract_name_from_text(user_text)
        if name is not None:
            # El usuario ya proporcionó nombre, guardarlo y continuar
            conversation = conversation.model_copy(update={"customer_name": name})
            logger.info("autonomous.name_extracted_in_first", name=name)
            # Continuar con el flujo normal (no retornar aquí)
        elif not conversation.customer_name:
            # No hay nombre y no se pudo extraer - PRIORIZAR preguntar por el nombre
            greeting = "¡Hola! Buenos días, soy el Asistente IA. Para comenzar, ¿podrías decirme tu nombre completo?"
            logger.info("autonomous.greeting.asking_name", greeting=greeting)
            return {**state, "response_text": greeting, "conversation": conversation}
        else:
            # Ya hay nombre (de memoria o BD) - saludo personalizado según si es recurrente
            format_message = "Formato esperado: día/mes hora o rango horario (se tomará en cuenta el año presente). Ejemplos: 15/01 18 horas, 15/01 2 PM, 15/01 18-20 horas"
            
            if is_recurring_customer and previous_bookings_count > 0:
                # Cliente recurrente con reservas previas - saludo más personalizado
                greeting = f"¡Hola {conversation.customer_name}! Me alegra verte de nuevo. Veo que ya has realizado {previous_bookings_count} reserva{'s' if previous_bookings_count > 1 else ''} anterior{'es' if previous_bookings_count > 1 else ''}. ¿Qué fecha y hora quisieras consultar para tu próxima reserva? {format_message}"
            else:
                # Cliente conocido pero sin reservas previas
                greeting = f"¡Hola {conversation.customer_name}! Buenos días, soy el Asistente IA, ¿qué fecha y hora quisieras consultar para reservar? {format_message}"
            
            logger.info("autonomous.greeting.asking_date_time", greeting=greeting, is_recurring=is_recurring_customer)
            return {**state, "response_text": greeting, "conversation": conversation}

    # Step 2: Detección de saludos comunes (después de la primera interacción)
    text_lower = user_text.lower().strip()
    saludos_comunes = {"hola", "hi", "hello", "buenos días", "buenos dias", "buenas tardes", "buenas noches"}
    if text_lower in saludos_comunes:
        # Si NO hay nombre, PRIORIZAR preguntar por el nombre
        if not conversation.customer_name:
            response = "¡Hola! Buenos días, soy el Asistente IA. Para comenzar, ¿podrías decirme tu nombre completo?"
            logger.info("autonomous.saludo_detectado.asking_name", user_text=user_text, response=response)
            return {**state, "response_text": response, "conversation": conversation}
        # Si YA hay nombre, preguntar por fecha y hora
        format_message = "Formato esperado: día/mes hora o rango horario (se tomará en cuenta el año presente). Ejemplos: 15/01 18 horas, 15/01 2 PM, 15/01 18-20 horas"
        response = f"¡Hola {conversation.customer_name}! Buenos días, soy el Asistente IA, ¿qué fecha y hora quisieras consultar para reservar? {format_message}"
        logger.info("autonomous.saludo_detectado.asking_date_time", user_text=user_text, response=response)
        return {**state, "response_text": response, "conversation": conversation}

    # Step 3: Capturar nombre del usuario (PRIORIDAD MÁXIMA - ANTES de procesar fecha/hora)
    # SIEMPRE verificar si tenemos nombre. Si no lo tenemos, pedirlo ANTES de procesar fecha/hora
    name = _extract_name_from_text(user_text)
    
    # Si no tenemos nombre en la base de datos
    if conversation.customer_name is None:
        if name is not None:
            # Se extrajo un nombre válido, guardarlo
            conversation = conversation.model_copy(update={"customer_name": name})
            logger.info("autonomous.name_extracted", name=name)
            # Continuar con el flujo para procesar también fecha/hora si está presente
        else:
            # No se pudo extraer nombre y no hay nombre en BD - PRIORIZAR pedir nombre
            # NO procesar fecha/hora hasta tener el nombre
            response = "Por favor, decime tu nombre completo para continuar."
            logger.info("autonomous.asking_name", user_text=user_text)
            return {**state, "response_text": response, "conversation": conversation}
    
    # Step 4: Extraer fecha y hora del texto si está presente (SOLO si ya tenemos nombre)
    parsed_date, parsed_start_time, parsed_end_time = _parse_date_and_time(user_text)
    extracted_date = parsed_date
    user_mentions_date = parsed_date is not None
    user_mentions_time = parsed_start_time is not None
    
    # Guardar la fecha y hora en la conversación si se encontraron
    if extracted_date:
        if conversation.requested_booking_date != extracted_date:
            conversation = conversation.model_copy(update={"requested_booking_date": extracted_date})
        if parsed_start_time and conversation.requested_booking_start_time != parsed_start_time:
            logger.info("autonomous.parsing.start_time", parsed=parsed_start_time, previous=conversation.requested_booking_start_time)
            conversation = conversation.model_copy(update={"requested_booking_start_time": parsed_start_time})
        if parsed_end_time and conversation.requested_booking_end_time != parsed_end_time:
            logger.info("autonomous.parsing.end_time", parsed=parsed_end_time, previous=conversation.requested_booking_end_time)
            conversation = conversation.model_copy(update={"requested_booking_end_time": parsed_end_time})
    
    # Detectar si el usuario está preguntando sobre disponibilidad/horarios
    availability_keywords = ["horarios", "disponibilidad", "disponible", "slots", "turnos", "agenda", "qué horas", "qué horarios"]
    user_asks_availability = any(keyword in user_text.lower() for keyword in availability_keywords)
    
    # Detectar si el usuario está confirmando una reserva
    confirmation_keywords = ["sí", "si", "confirmo", "confirmar", "ok", "okay", "de acuerdo", "perfecto", "vamos", "adelante"]
    user_confirms = any(keyword in user_text.lower() for keyword in confirmation_keywords)
    
    # Si se extrajo nombre y no hay fecha/hora, preguntar por fecha y hora
    if conversation.customer_name and name is not None and not user_mentions_date and not user_mentions_time:
        format_message = "Formato esperado: día/mes hora o rango horario (se tomará en cuenta el año presente). Ejemplos: 15/01 18 horas, 15/01 2 PM, 15/01 18-20 horas"
        response = f"Mucho gusto, {conversation.customer_name}. ¿Qué fecha y hora quisieras consultar para reservar? {format_message}"
        logger.info("autonomous.name_extracted.asking_date_time", name=conversation.customer_name, response=response)
        return {**state, "response_text": response, "conversation": conversation}
    
    # Si ya tenemos nombre pero se proporciona uno nuevo, actualizarlo
    if name is not None and conversation.customer_name and name.lower() != conversation.customer_name.lower():
        conversation = conversation.model_copy(update={"customer_name": name})
        # Continuar con el flujo normal (no retornar aquí, dejar que el planner procese)
    
    # Preparar fecha y hora para pasar al planner
    date_to_pass = None
    start_time_to_pass = None
    end_time_to_pass = None
    
    if user_mentions_date:
        date_to_pass = extracted_date or conversation.requested_booking_date
        start_time_to_pass = parsed_start_time or conversation.requested_booking_start_time
        end_time_to_pass = parsed_end_time or conversation.requested_booking_end_time
    elif user_asks_availability and conversation.requested_booking_date:
        date_to_pass = conversation.requested_booking_date
        start_time_to_pass = conversation.requested_booking_start_time
        end_time_to_pass = conversation.requested_booking_end_time
    elif user_confirms and conversation.requested_booking_date and conversation.requested_booking_start_time and conversation.requested_booking_end_time:
        # Si el usuario confirma y tenemos fecha/hora en el contexto, pasarlas al planner
        date_to_pass = conversation.requested_booking_date
        start_time_to_pass = conversation.requested_booking_start_time
        end_time_to_pass = conversation.requested_booking_end_time
        logger.info("autonomous.user_confirms_with_context", date=date_to_pass, start_time=start_time_to_pass, end_time=end_time_to_pass)
    # Si no se cumple ninguna condición, no pasar fecha/hora (None)

    # Step 5: Usar planner para generar plan (incluir contexto de reservas previas)
    logger.info("autonomous.llamando_planner", user_text=user_text, customer_name=conversation.customer_name, 
                date=date_to_pass, is_recurring=is_recurring_customer, previous_bookings=previous_bookings_count)
    plan = planner.plan(
        user_text=user_text,
        customer_id=customer_id,
        customer_name=conversation.customer_name,
        requested_booking_date=date_to_pass,
        requested_booking_start_time=start_time_to_pass,
        requested_booking_end_time=end_time_to_pass,
        previous_bookings_summary=previous_bookings_summary if previous_bookings_summary else None,
        is_recurring_customer=is_recurring_customer,
    )

    if plan is None or not plan.actions:
        logger.warning("autonomous.planner.no_plan")
        return {**state, "response_text": "No pude entender tu solicitud. ¿Podrías reformularla?", "conversation": conversation}

    logger.info("autonomous.plan_generado", actions_count=len(plan.actions), actions=[a.type for a in plan.actions])

    # Step 6: Ejecutar acciones del plan
    for action in plan.actions:
        if action.type == "ask_user":
            logger.info("autonomous.ask_user", text=action.text)
            return {**state, "response_text": action.text, "conversation": conversation}

        if action.type == "tool_call":
            # Guardar fecha si está en los args antes de ejecutar
            if "date_iso" in action.args and isinstance(action.args["date_iso"], str):
                date_iso_from_args = action.args["date_iso"].strip()
                if date_iso_from_args and conversation.requested_booking_date != date_iso_from_args:
                    conversation = conversation.model_copy(update={"requested_booking_date": date_iso_from_args})
            
            # Ejecutar función según el tool
            if action.tool == "get_available_slots":
                date_iso = action.args.get("date_iso") or conversation.requested_booking_date or extracted_date
                if not isinstance(date_iso, str) or date_iso.strip() == "":
                    return {
                        **state,
                        "response_text": "Necesito la fecha para consultar disponibilidad. ¿Qué fecha te interesa?",
                        "conversation": conversation,
                    }
                slots_out = get_available_slots(GetAvailableSlotsInput(date_iso=date_iso, customer_id=customer_id))
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
                conversation = conversation.model_copy(update={"requested_booking_date": date_iso})
                return {**state, "response_text": "\n".join(lines), "conversation": conversation}

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
                        date_iso=date_iso, start_time_iso=start_time_iso, end_time_iso=end_time_iso, customer_id=customer_id
                    )
                )
                logger.info("autonomous.check_availability", date_iso=date_iso, customer_id=customer_id, available=availability_out.available)
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
                
                # VERIFICAR DISPONIBILIDAD ANTES DE CREAR LA RESERVA
                availability_out = check_availability(
                    CheckAvailabilityInput(
                        date_iso=booking_date, start_time_iso=booking_start, end_time_iso=booking_end, customer_id=customer_id
                    )
                )
                if availability_out.error_code is not None:
                    return {
                        **state,
                        "response_text": "No pude verificar la disponibilidad en este momento. Probá de nuevo en unos minutos.",
                        "conversation": conversation,
                    }
                if not availability_out.available:
                    start = booking_start.split("T")[1].split(":")[:2]
                    end = booking_end.split("T")[1].split(":")[:2]
                    return {
                        **state,
                        "response_text": f"Lo siento, el horario del {booking_date} de {':'.join(start)} a {':'.join(end)} ya no está disponible. Por favor, consultá otros horarios.",
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

            if action.tool == "get_booking":
                booking_id = action.args.get("booking_id")
                if not isinstance(booking_id, str) or booking_id.strip() == "":
                    return {
                        **state,
                        "response_text": "Necesito el ID de la reserva para consultarla. ¿Cuál es el ID de tu reserva?",
                        "conversation": conversation,
                    }
                booking_out = get_booking(GetBookingInput(booking_id=booking_id))
                if not booking_out.found:
                    return {
                        **state,
                        "response_text": f"No encontré la reserva {booking_id}. Verificá el ID e intentá de nuevo.",
                        "conversation": conversation,
                    }
                start = booking_out.start_time_iso.split("T")[1].split(":")[:2] if booking_out.start_time_iso else ["", ""]
                end = booking_out.end_time_iso.split("T")[1].split(":")[:2] if booking_out.end_time_iso else ["", ""]
                response = (
                    f"Reserva {booking_out.booking_id}:\n"
                    f"- Cliente: {booking_out.customer_name}\n"
                    f"- Fecha: {booking_out.date_iso}\n"
                    f"- Horario: {':'.join(start)} a {':'.join(end)}\n"
                    f"- Estado: {booking_out.status}"
                )
                return {**state, "response_text": response, "conversation": conversation}

            if action.tool == "list_bookings":
                if customer_id is None:
                    return {
                        **state,
                        "response_text": "Necesito tu identificador de cliente para consultar tus reservas.",
                        "conversation": conversation,
                    }
                bookings_out = list_bookings(ListBookingsInput(customer_id=customer_id))
                if bookings_out.error_code is not None:
                    return {
                        **state,
                        "response_text": "No pude consultar tus reservas en este momento. Probá de nuevo en unos minutos.",
                        "conversation": conversation,
                    }
                if len(bookings_out.bookings) == 0:
                    return {
                        **state,
                        "response_text": "No tenés reservas registradas. ¿Querés hacer una nueva reserva?",
                        "conversation": conversation,
                    }
                lines = ["Tus reservas:"]
                for booking in bookings_out.bookings[:10]:
                    start = booking.start_time_iso.split("T")[1].split(":")[:2] if booking.start_time_iso else ["", ""]
                    end = booking.end_time_iso.split("T")[1].split(":")[:2] if booking.end_time_iso else ["", ""]
                    lines.append(
                        f"- {booking.booking_id}: {booking.date_iso} de {':'.join(start)} a {':'.join(end)} ({booking.status})"
                    )
                return {**state, "response_text": "\n".join(lines), "conversation": conversation}

            if action.tool == "update_booking":
                booking_id = action.args.get("booking_id")
                if not isinstance(booking_id, str) or booking_id.strip() == "":
                    return {
                        **state,
                        "response_text": "Necesito el ID de la reserva para actualizarla. ¿Cuál es el ID de tu reserva?",
                        "conversation": conversation,
                    }
                update_input = UpdateBookingInput(booking_id=booking_id)
                if "date_iso" in action.args:
                    update_input.date_iso = action.args["date_iso"]
                if "start_time_iso" in action.args:
                    update_input.start_time_iso = action.args["start_time_iso"]
                if "end_time_iso" in action.args:
                    update_input.end_time_iso = action.args["end_time_iso"]
                if "status" in action.args:
                    update_input.status = action.args["status"]
                update_out = update_booking(update_input)
                if not update_out.success:
                    return {
                        **state,
                        "response_text": "No pude actualizar la reserva en este momento. Probá de nuevo en unos minutos.",
                        "conversation": conversation,
                    }
                response = f"Reserva {booking_id} actualizada exitosamente."
                return {**state, "response_text": response, "conversation": conversation}

            if action.tool == "delete_booking":
                booking_id = action.args.get("booking_id")
                if not isinstance(booking_id, str) or booking_id.strip() == "":
                    return {
                        **state,
                        "response_text": "Necesito el ID de la reserva para cancelarla. ¿Cuál es el ID de tu reserva?",
                        "conversation": conversation,
                    }
                delete_out = delete_booking(DeleteBookingInput(booking_id=booking_id))
                if not delete_out.success:
                    return {
                        **state,
                        "response_text": "No pude cancelar la reserva en este momento. Probá de nuevo en unos minutos.",
                        "conversation": conversation,
                    }
                response = f"Reserva {booking_id} cancelada exitosamente."
                return {**state, "response_text": response, "conversation": conversation}

            if action.tool == "vector_recall":
                if customer_id is None:
                    return {
                        **state,
                        "response_text": "Necesito tu identificador de cliente para buscar en tus reservas.",
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

    # Fallback
    return {**state, "response_text": f"Hola {conversation.customer_name}, ¿en qué puedo ayudarte?", "conversation": conversation}


def unknown_node(state: GraphState) -> GraphState:
    """Fallback handler when the domain cannot be determined."""
    user_text = state["user_text"].strip().lower()
    conversation = state["conversation"]
    
    # Detectar si el usuario escribió "menu"
    if user_text == "menu" or user_text == "menú":
        flows = _get_active_flows()
        menu_data = _show_menu(flows)
        # Guardar los flujos en memoria para poder mapear números después
        updated_memory = dict(conversation.customer_memory)
        updated_memory["menu_flows"] = json.dumps(flows)
        updated_conversation = conversation.model_copy(update={"customer_memory": updated_memory})
        return {
            **state,
            "conversation": updated_conversation,
            "response_text": menu_data.get("text", ""),
            "interactive_type": menu_data.get("interactive_type"),
            "buttons": menu_data.get("buttons"),
            "list_title": menu_data.get("list_title"),
            "list_items": menu_data.get("list_items"),
        }
    
    
    # Respuesta por defecto
    return {
        **state,
        "response_text": "¿Querés hacer una reserva, revisar una compra, o iniciar un reclamo? Contame un poco más.\n\nO escribe *menu* o *menú* para ver todas las opciones disponibles.",
    }


def build_router_graph(router_fn: RouterFn | None = None) -> StateGraph[GraphState]:
    """Build the top-level router graph that delegates to domain handlers."""
    router = router_fn or route_domain
    graph = StateGraph(GraphState)
    graph.add_node("route", _make_route_node(router))
    graph.add_node("purchases", purchases_node)
    graph.add_node("bookings", bookings_node)
    graph.add_node("claims", claims_node)
    graph.add_node("autonomous", autonomous_node)
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
            "autonomous": "autonomous",
            "unknown": "unknown",
        },
    )
    graph.add_edge("purchases", END)
    graph.add_edge("bookings", END)
    graph.add_edge("claims", END)
    graph.add_edge("autonomous", END)
    graph.add_edge("unknown", END)
    return graph


