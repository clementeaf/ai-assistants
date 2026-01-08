from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from ai_assistants.adapters.professionals import ProfessionalsAdapter
from ai_assistants.domain.professionals.models import Area, Professional, Specialty


class MCPProfessionalsAdapter(ProfessionalsAdapter):
    """Adapter that connects to a professionals service via MCP (Model Context Protocol)."""

    def __init__(self, mcp_server_url: str, api_key: str | None = None, timeout_seconds: float = 10.0) -> None:
        self._mcp_url = mcp_server_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout_seconds
        self._client = httpx.Client(timeout=timeout_seconds)

    def _call_mcp_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call an MCP tool and return the result."""
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
        }

        response = self._client.post(
            f"{self._mcp_url}/mcp",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        json_response = response.json()
        if "error" in json_response and json_response["error"] is not None:
            error_msg = json_response["error"].get("message", "Unknown error")
            raise ValueError(f"MCP error: {error_msg}")
        return json_response.get("result", {})

    def _parse_datetime(self, dt_str: str | None) -> datetime:
        """Parse datetime string to datetime object."""
        if dt_str is None:
            return datetime.now()
        if isinstance(dt_str, str):
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return datetime.now()

    def create_area(self, name: str, description: str | None = None) -> Area:
        """Create a new area."""
        result = self._call_mcp_tool("create_area", {"name": name, "description": description})
        area_data = result.get("area", {})
        return Area(
            area_id=area_data["area_id"],
            name=area_data["name"],
            description=area_data.get("description"),
            created_at=self._parse_datetime(area_data.get("created_at")),
        )

    def get_area(self, area_id: str) -> Area | None:
        """Get an area by ID."""
        result = self._call_mcp_tool("get_area", {"area_id": area_id})
        area_data = result.get("area")
        if area_data is None:
            return None
        return Area(
            area_id=area_data["area_id"],
            name=area_data["name"],
            description=area_data.get("description"),
            created_at=self._parse_datetime(area_data.get("created_at")),
        )

    def list_areas(self) -> list[Area]:
        """List all areas."""
        result = self._call_mcp_tool("list_areas", {})
        areas_data = result.get("areas", [])
        return [
            Area(
                area_id=a["area_id"],
                name=a["name"],
                description=a.get("description"),
                created_at=self._parse_datetime(a.get("created_at")),
            )
            for a in areas_data
        ]

    def create_specialty(self, name: str, area_id: str | None = None, description: str | None = None) -> Specialty:
        """Create a new specialty."""
        args: dict[str, Any] = {"name": name}
        if area_id is not None:
            args["area_id"] = area_id
        if description is not None:
            args["description"] = description
        result = self._call_mcp_tool("create_specialty", args)
        spec_data = result.get("specialty", {})
        return Specialty(
            specialty_id=spec_data["specialty_id"],
            name=spec_data["name"],
            description=spec_data.get("description"),
            area_id=spec_data.get("area_id"),
            created_at=self._parse_datetime(spec_data.get("created_at")),
        )

    def get_specialty(self, specialty_id: str) -> Specialty | None:
        """Get a specialty by ID."""
        result = self._call_mcp_tool("get_specialty", {"specialty_id": specialty_id})
        spec_data = result.get("specialty")
        if spec_data is None:
            return None
        return Specialty(
            specialty_id=spec_data["specialty_id"],
            name=spec_data["name"],
            description=spec_data.get("description"),
            area_id=spec_data.get("area_id"),
            created_at=self._parse_datetime(spec_data.get("created_at")),
        )

    def list_specialties(self, area_id: str | None = None) -> list[Specialty]:
        """List specialties, optionally filtered by area."""
        args: dict[str, Any] = {}
        if area_id is not None:
            args["area_id"] = area_id
        result = self._call_mcp_tool("list_specialties", args)
        specs_data = result.get("specialties", [])
        return [
            Specialty(
                specialty_id=s["specialty_id"],
                name=s["name"],
                description=s.get("description"),
                area_id=s.get("area_id"),
                created_at=self._parse_datetime(s.get("created_at")),
            )
            for s in specs_data
        ]

    def create_professional(self, name: str, email: str | None = None, phone: str | None = None) -> Professional:
        """Create a new professional."""
        args: dict[str, Any] = {"name": name}
        if email is not None:
            args["email"] = email
        if phone is not None:
            args["phone"] = phone
        result = self._call_mcp_tool("create_professional", args)
        prof_data = result.get("professional", {})
        specialties = [
            Specialty(
                specialty_id=s["specialty_id"],
                name=s["name"],
                description=s.get("description"),
                area_id=s.get("area_id"),
                created_at=datetime.now(),
            )
            for s in prof_data.get("specialties", [])
        ]
        return Professional(
            professional_id=prof_data["professional_id"],
            name=prof_data["name"],
            email=prof_data.get("email"),
            phone=prof_data.get("phone"),
            active=prof_data.get("active", True),
            created_at=self._parse_datetime(prof_data.get("created_at")),
            specialties=specialties,
        )

    def get_professional(self, professional_id: str) -> Professional | None:
        """Get a professional by ID."""
        result = self._call_mcp_tool("get_professional", {"professional_id": professional_id})
        prof_data = result.get("professional")
        if prof_data is None:
            return None
        specialties = [
            Specialty(
                specialty_id=s["specialty_id"],
                name=s["name"],
                description=s.get("description"),
                area_id=s.get("area_id"),
                created_at=datetime.now(),
            )
            for s in prof_data.get("specialties", [])
        ]
        return Professional(
            professional_id=prof_data["professional_id"],
            name=prof_data["name"],
            email=prof_data.get("email"),
            phone=prof_data.get("phone"),
            active=prof_data.get("active", True),
            created_at=self._parse_datetime(prof_data.get("created_at")),
            specialties=specialties,
        )

    def list_professionals(self, specialty_id: str | None = None, area_id: str | None = None) -> list[Professional]:
        """List professionals, optionally filtered by specialty or area."""
        args: dict[str, Any] = {}
        if specialty_id is not None:
            args["specialty_id"] = specialty_id
        if area_id is not None:
            args["area_id"] = area_id
        result = self._call_mcp_tool("list_professionals", args)
        profs_data = result.get("professionals", [])
        return [
            Professional(
                professional_id=p["professional_id"],
                name=p["name"],
                email=p.get("email"),
                phone=p.get("phone"),
                active=p.get("active", True),
                created_at=self._parse_datetime(p.get("created_at")),
                specialties=[],  # List endpoint doesn't include specialties
            )
            for p in profs_data
        ]

    def assign_specialty(self, professional_id: str, specialty_id: str) -> bool:
        """Assign a specialty to a professional."""
        result = self._call_mcp_tool("assign_specialty", {"professional_id": professional_id, "specialty_id": specialty_id})
        return result.get("success", False)

    def remove_specialty(self, professional_id: str, specialty_id: str) -> bool:
        """Remove a specialty from a professional."""
        result = self._call_mcp_tool("remove_specialty", {"professional_id": professional_id, "specialty_id": specialty_id})
        return result.get("success", False)

    def update_professional(
        self,
        professional_id: str,
        name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        active: bool | None = None,
    ) -> Professional | None:
        """Update a professional."""
        args: dict[str, Any] = {"professional_id": professional_id}
        if name is not None:
            args["name"] = name
        if email is not None:
            args["email"] = email
        if phone is not None:
            args["phone"] = phone
        if active is not None:
            args["active"] = active
        result = self._call_mcp_tool("update_professional", args)
        prof_data = result.get("professional")
        if prof_data is None:
            return None
        specialties = [
            Specialty(
                specialty_id=s["specialty_id"],
                name=s["name"],
                description=s.get("description"),
                area_id=s.get("area_id"),
                created_at=datetime.now(),
            )
            for s in prof_data.get("specialties", [])
        ]
        return Professional(
            professional_id=prof_data["professional_id"],
            name=prof_data["name"],
            email=prof_data.get("email"),
            phone=prof_data.get("phone"),
            active=prof_data.get("active", True),
            created_at=self._parse_datetime(prof_data.get("created_at")),
            specialties=specialties,
        )

    def delete_professional(self, professional_id: str) -> bool:
        """Delete (deactivate) a professional."""
        result = self._call_mcp_tool("delete_professional", {"professional_id": professional_id})
        return result.get("success", False)

