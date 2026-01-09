"""Tests for tool functions."""

from __future__ import annotations

import pytest

from ai_assistants.tools.bookings_tools import (
    check_availability,
    create_booking,
    get_available_slots,
    get_booking,
    list_bookings,
)
from ai_assistants.tools.contracts import (
    CheckAvailabilityInput,
    CreateBookingInput,
    GetAvailableSlotsInput,
    GetBookingInput,
    ListBookingsInput,
)
from ai_assistants.tools.purchases_tools import get_order, get_tracking_status, list_orders
from ai_assistants.tools.contracts import GetOrderInput, GetTrackingInput, ListOrdersInput


def test_get_available_slots(demo_adapters) -> None:
    """Test getting available booking slots."""
    input_data = GetAvailableSlotsInput(date_iso="2025-03-15")
    result = get_available_slots(input_data)
    
    assert result.error_code is None
    assert len(result.slots) > 0
    assert all(slot.available for slot in result.slots)


def test_check_availability(demo_adapters) -> None:
    """Test checking availability for a specific time slot."""
    input_data = CheckAvailabilityInput(
        date_iso="2025-03-15",
        start_time_iso="2025-03-15T09:00:00Z",
        end_time_iso="2025-03-15T10:00:00Z",
    )
    result = check_availability(input_data)
    
    assert result.error_code is None
    assert isinstance(result.available, bool)


def test_create_booking(demo_adapters) -> None:
    """Test creating a booking."""
    input_data = CreateBookingInput(
        customer_id="+5491112345678",
        customer_name="Test User",
        date_iso="2025-03-15",
        start_time_iso="2025-03-15T09:00:00Z",
        end_time_iso="2025-03-15T10:00:00Z",
    )
    result = create_booking(input_data)
    
    assert result.success is True
    assert result.booking_id is not None
    assert result.error_code is None


def test_get_booking(demo_adapters) -> None:
    """Test getting a booking by ID."""
    first = create_booking(
        CreateBookingInput(
            customer_id="+5491112345678",
            customer_name="Test User",
            date_iso="2025-03-15",
            start_time_iso="2025-03-15T09:00:00Z",
            end_time_iso="2025-03-15T10:00:00Z",
        )
    )
    
    if first.success and first.booking_id:
        input_data = GetBookingInput(booking_id=first.booking_id)
        result = get_booking(input_data)
        
        assert result.found is True
        assert result.booking_id == first.booking_id
        assert result.error_code is None


def test_list_bookings(demo_adapters) -> None:
    """Test listing bookings for a customer."""
    customer_id = "+5491112345678"
    
    create_booking(
        CreateBookingInput(
            customer_id=customer_id,
            customer_name="Test User",
            date_iso="2025-03-15",
            start_time_iso="2025-03-15T09:00:00Z",
            end_time_iso="2025-03-15T10:00:00Z",
        )
    )
    
    input_data = ListBookingsInput(customer_id=customer_id)
    result = list_bookings(input_data)
    
    assert result.error_code is None
    assert len(result.bookings) > 0
    assert all(booking.customer_id == customer_id for booking in result.bookings)


def test_get_order(demo_adapters) -> None:
    """Test getting an order by ID."""
    input_data = GetOrderInput(order_id="ORDER-100")
    result = get_order(input_data)
    
    assert result.found is True
    assert result.order_id == "ORDER-100"
    assert result.error_code is None


def test_list_orders(demo_adapters) -> None:
    """Test listing orders for a customer."""
    input_data = ListOrdersInput(customer_id="customer-123")
    result = list_orders(input_data)
    
    assert result.error_code is None
    assert len(result.orders) > 0
    assert all(order.customer_id == "customer-123" for order in result.orders)


def test_get_tracking_status(demo_adapters) -> None:
    """Test getting tracking status."""
    input_data = GetTrackingInput(tracking_id="TRACK-9002")
    result = get_tracking_status(input_data)
    
    assert result.found is True
    assert result.tracking_id == "TRACK-9002"
    assert result.error_code is None
