"""Tests for routing functionality."""

from __future__ import annotations

from ai_assistants.routing.domain_router import Domain, route_domain, route_domain_rules


def test_route_domain_rules_bookings() -> None:
    """Test routing to bookings domain."""
    assert route_domain_rules("Quiero hacer una reserva") == "bookings"
    assert route_domain_rules("Necesito un turno") == "bookings"
    assert route_domain_rules("agenda") == "bookings"


def test_route_domain_rules_purchases() -> None:
    """Test routing to purchases domain."""
    assert route_domain_rules("Quiero ver mi compra") == "purchases"
    assert route_domain_rules("ORDER-100") == "purchases"
    assert route_domain_rules("TRACK-9002") == "purchases"
    assert route_domain_rules("seguimiento") == "purchases"


def test_route_domain_rules_claims() -> None:
    """Test routing to claims domain."""
    assert route_domain_rules("Quiero hacer un reclamo") == "claims"
    assert route_domain_rules("devolución") == "claims"


def test_route_domain_rules_menu() -> None:
    """Test routing to unknown domain for menu."""
    assert route_domain_rules("menu") == "unknown"
    assert route_domain_rules("menú") == "unknown"


def test_route_domain_rules_default() -> None:
    """Test default routing behavior."""
    assert route_domain_rules("Hola") == "bookings"
    assert route_domain_rules("") == "bookings"
