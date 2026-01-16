"""
Autómata de Compras (Purchases)
Gestiona consultas de órdenes, seguimiento de envíos y compras del cliente.
"""

from __future__ import annotations

from ai_assistants.automata.purchases.planner import PurchasesPlanner, build_purchases_planner_from_env
from ai_assistants.automata.purchases.runtime import get_purchases_planner, set_purchases_planner

__all__ = [
    "PurchasesPlanner",
    "build_purchases_planner_from_env",
    "get_purchases_planner",
    "set_purchases_planner",
]
