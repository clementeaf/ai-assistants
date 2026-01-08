from __future__ import annotations

from typing import Protocol

from ai_assistants.domain.professionals.models import Area, Professional, Specialty


class ProfessionalsAdapter(Protocol):
    """Adapter interface for professionals, areas, and specialties operations."""

    def create_area(self, name: str, description: str | None = None) -> Area:
        """Create a new area."""

    def get_area(self, area_id: str) -> Area | None:
        """Get an area by ID."""

    def list_areas(self) -> list[Area]:
        """List all areas."""

    def create_specialty(self, name: str, area_id: str | None = None, description: str | None = None) -> Specialty:
        """Create a new specialty."""

    def get_specialty(self, specialty_id: str) -> Specialty | None:
        """Get a specialty by ID."""

    def list_specialties(self, area_id: str | None = None) -> list[Specialty]:
        """List specialties, optionally filtered by area."""

    def create_professional(self, name: str, email: str | None = None, phone: str | None = None) -> Professional:
        """Create a new professional."""

    def get_professional(self, professional_id: str) -> Professional | None:
        """Get a professional by ID."""

    def list_professionals(self, specialty_id: str | None = None, area_id: str | None = None) -> list[Professional]:
        """List professionals, optionally filtered by specialty or area."""

    def assign_specialty(self, professional_id: str, specialty_id: str) -> bool:
        """Assign a specialty to a professional. Returns True if successful."""

    def remove_specialty(self, professional_id: str, specialty_id: str) -> bool:
        """Remove a specialty from a professional. Returns True if successful."""

    def update_professional(
        self,
        professional_id: str,
        name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        active: bool | None = None,
    ) -> Professional | None:
        """Update a professional. Returns the updated professional or None if not found."""

    def delete_professional(self, professional_id: str) -> bool:
        """Delete (deactivate) a professional. Returns True if successful."""

