from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Area:
    """Area entity."""

    area_id: str
    name: str
    description: str | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class Specialty:
    """Specialty entity."""

    specialty_id: str
    name: str
    description: str | None
    area_id: str | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class Professional:
    """Professional entity."""

    professional_id: str
    name: str
    email: str | None
    phone: str | None
    active: bool
    created_at: datetime
    specialties: list[Specialty]

