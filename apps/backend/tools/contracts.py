from __future__ import annotations

from pydantic import BaseModel, Field


class GetOrderInput(BaseModel):
    """Input contract for the get-order tool."""

    order_id: str = Field(min_length=1)


class GetOrderOutput(BaseModel):
    """Output contract for the get-order tool."""

    found: bool
    order_id: str | None
    customer_id: str | None
    status: str | None
    total_amount: float | None
    currency: str | None
    created_at_iso: str | None
    tracking_id: str | None
    error_code: str | None = None


class ListOrdersInput(BaseModel):
    """Input contract for listing orders of a customer."""

    customer_id: str = Field(min_length=1)


class OrderSummary(BaseModel):
    """Order summary used in list outputs."""

    order_id: str
    status: str
    total_amount: float
    currency: str
    created_at_iso: str
    tracking_id: str | None


class ListOrdersOutput(BaseModel):
    """Output contract for listing orders."""

    orders: list[OrderSummary]
    error_code: str | None = None


class GetTrackingInput(BaseModel):
    """Input contract for tracking status lookup."""

    order_id: str | None = None
    tracking_id: str | None = None


class GetTrackingOutput(BaseModel):
    """Output contract for shipment tracking."""

    found: bool
    tracking_id: str | None
    order_id: str | None
    carrier: str | None
    status: str | None
    last_update_iso: str | None
    estimated_delivery_iso: str | None
    error_code: str | None = None


class CheckAvailabilityInput(BaseModel):
    """Input contract for checking booking availability."""

    date_iso: str = Field(min_length=1)
    start_time_iso: str = Field(min_length=1)
    end_time_iso: str = Field(min_length=1)
    customer_id: str | None = None


class CheckAvailabilityOutput(BaseModel):
    """Output contract for availability check."""

    available: bool
    error_code: str | None = None


class GetAvailableSlotsInput(BaseModel):
    """Input contract for getting available booking slots."""

    date_iso: str = Field(min_length=1)
    customer_id: str | None = None


class BookingSlotSummary(BaseModel):
    """Booking slot summary used in list outputs."""

    date_iso: str
    start_time_iso: str
    end_time_iso: str
    available: bool


class GetAvailableSlotsOutput(BaseModel):
    """Output contract for listing available slots."""

    slots: list[BookingSlotSummary]
    error_code: str | None = None


class CreateBookingInput(BaseModel):
    """Input contract for creating a booking."""

    customer_id: str = Field(min_length=1)
    customer_name: str = Field(min_length=1)
    date_iso: str = Field(min_length=1)
    start_time_iso: str = Field(min_length=1)
    end_time_iso: str = Field(min_length=1)


class CreateBookingOutput(BaseModel):
    """Output contract for creating a booking."""

    success: bool
    booking_id: str | None = None
    date_iso: str | None = None
    start_time_iso: str | None = None
    end_time_iso: str | None = None
    error_code: str | None = None


class GetBookingInput(BaseModel):
    """Input contract for getting a booking by ID."""

    booking_id: str = Field(min_length=1)


class GetBookingOutput(BaseModel):
    """Output contract for getting a booking."""

    found: bool
    booking_id: str | None
    customer_id: str | None
    customer_name: str | None
    date_iso: str | None
    start_time_iso: str | None
    end_time_iso: str | None
    status: str | None
    created_at_iso: str | None
    error_code: str | None = None


class ListBookingsInput(BaseModel):
    """Input contract for listing bookings of a customer."""

    customer_id: str = Field(min_length=1)


class BookingSummary(BaseModel):
    """Booking summary used in list outputs."""

    booking_id: str
    customer_id: str
    customer_name: str
    date_iso: str
    start_time_iso: str
    end_time_iso: str
    status: str
    created_at_iso: str


class ListBookingsOutput(BaseModel):
    """Output contract for listing bookings."""

    bookings: list[BookingSummary]
    error_code: str | None = None


class UpdateBookingInput(BaseModel):
    """Input contract for updating a booking."""

    booking_id: str = Field(min_length=1)
    date_iso: str | None = None
    start_time_iso: str | None = None
    end_time_iso: str | None = None
    status: str | None = None


class UpdateBookingOutput(BaseModel):
    """Output contract for updating a booking."""

    success: bool
    booking_id: str | None
    date_iso: str | None
    start_time_iso: str | None
    end_time_iso: str | None
    status: str | None
    error_code: str | None = None


class DeleteBookingInput(BaseModel):
    """Input contract for deleting a booking."""

    booking_id: str = Field(min_length=1)


class DeleteBookingOutput(BaseModel):
    """Output contract for deleting a booking."""

    success: bool
    booking_id: str | None
    error_code: str | None = None


