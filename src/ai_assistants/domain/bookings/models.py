from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class BookingStatus(str, Enum):
    """Supported booking statuses."""

    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"


@dataclass(frozen=True, slots=True)
class BookingSlot:
    """Available time slot for booking."""

    date_iso: str
    start_time_iso: str
    end_time_iso: str
    available: bool


@dataclass(frozen=True, slots=True)
class Booking:
    """Booking/reservation entity."""

    booking_id: str
    customer_id: str
    customer_name: str
    date_iso: str
    start_time_iso: str
    end_time_iso: str
    status: BookingStatus
    created_at: datetime
    confirmation_email_sent: bool
    reminder_sent: bool

