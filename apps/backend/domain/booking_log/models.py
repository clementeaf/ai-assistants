from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class BookingLog:
    """Booking log entry entity."""

    log_id: str
    booking_code: str
    customer_name: str
    customer_id: str | None
    date_iso: str
    time_iso: str
    area_id: str | None
    area_name: str | None
    specialty_id: str | None
    specialty_name: str | None
    professional_id: str | None
    professional_name: str | None
    observations: str | None
    created_at: datetime
    updated_at: datetime

