from __future__ import annotations

import os
import time
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Callable
from enum import Enum

import httpx
from pydantic import BaseModel, Field
from structlog.contextvars import get_contextvars

from ai_assistants.adapters.purchases import PurchasesAdapter
from ai_assistants.channels.webhook_security import compute_signature
from ai_assistants.domain.purchases.models import Order, OrderStatus, Shipment, ShipmentStatus
from ai_assistants.observability.logging import get_logger


class HookAction(str, Enum):
    """Supported actions for the purchases hook API."""

    get_order = "get_order"
    list_orders = "list_orders"
    get_shipment_by_order_id = "get_shipment_by_order_id"
    get_shipment_by_tracking_id = "get_shipment_by_tracking_id"


class HookRequest(BaseModel):
    """Request envelope sent to an external purchases hook."""

    action: HookAction
    payload: dict[str, str] = Field(default_factory=dict)


class HookOrder(BaseModel):
    """Order payload returned by the external hook."""

    order_id: str
    customer_id: str
    status: OrderStatus
    total_amount: float
    currency: str
    created_at_iso: str

    def to_domain(self) -> Order:
        """Convert to domain Order."""
        return Order(
            order_id=self.order_id,
            customer_id=self.customer_id,
            status=self.status,
            total_amount=self.total_amount,
            currency=self.currency,
            created_at=datetime.fromisoformat(self.created_at_iso),
        )


class HookShipment(BaseModel):
    """Shipment payload returned by the external hook."""

    tracking_id: str
    order_id: str
    carrier: str
    status: ShipmentStatus
    last_update_at_iso: str
    estimated_delivery_at_iso: str | None

    def to_domain(self) -> Shipment:
        """Convert to domain Shipment."""
        return Shipment(
            tracking_id=self.tracking_id,
            order_id=self.order_id,
            carrier=self.carrier,
            status=self.status,
            last_update_at=datetime.fromisoformat(self.last_update_at_iso),
            estimated_delivery_at=datetime.fromisoformat(self.estimated_delivery_at_iso)
            if self.estimated_delivery_at_iso
            else None,
        )


class HookResponse(BaseModel):
    """Response envelope returned by the external purchases hook."""

    ok: bool
    error_code: str | None = None
    error_message: str | None = None
    order: HookOrder | None = None
    orders: list[HookOrder] | None = None
    shipment: HookShipment | None = None


@dataclass(frozen=True, slots=True)
class ExternalHookConfig:
    """External hook configuration."""

    url: str
    timeout_seconds: float
    api_key: str | None
    signature_secret: str | None
    max_retries: int


def load_external_hook_config() -> ExternalHookConfig | None:
    """Load external purchases hook config from env vars.

    If AI_ASSISTANTS_PURCHASES_HOOK_URL is not set, returns None (disabled).
    """
    url = os.getenv("AI_ASSISTANTS_PURCHASES_HOOK_URL")
    if url is None or url.strip() == "":
        return None
    timeout_raw = os.getenv("AI_ASSISTANTS_PURCHASES_HOOK_TIMEOUT_SECONDS", "5")
    try:
        timeout_seconds = float(timeout_raw)
    except ValueError:
        timeout_seconds = 5.0
    api_key = os.getenv("AI_ASSISTANTS_PURCHASES_HOOK_API_KEY")
    signature_secret = os.getenv("AI_ASSISTANTS_PURCHASES_HOOK_SIGNATURE_SECRET")
    retries_raw = os.getenv("AI_ASSISTANTS_PURCHASES_HOOK_MAX_RETRIES", "2")
    try:
        max_retries = int(retries_raw)
    except ValueError:
        max_retries = 2
    if max_retries < 0:
        max_retries = 0
    return ExternalHookConfig(
        url=url,
        timeout_seconds=timeout_seconds,
        api_key=api_key,
        signature_secret=signature_secret,
        max_retries=max_retries,
    )


class ExternalHookPurchasesAdapter(PurchasesAdapter):
    """Purchases adapter backed by an external API hook."""

    class HookUnavailableError(RuntimeError):
        """Raised when the external purchases hook is unavailable (transient failure)."""

    def __init__(
        self,
        config: ExternalHookConfig,
        client: httpx.Client | None = None,
        now_fn: Callable[[], float] | None = None,
    ) -> None:
        self._config = config
        self._logger = get_logger()
        self._client = client or httpx.Client(timeout=config.timeout_seconds)
        self._now_fn = now_fn or time.time

    def _build_headers(self, body_bytes: bytes) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._config.api_key is not None and self._config.api_key.strip() != "":
            headers["X-API-Key"] = self._config.api_key
        ctx = get_contextvars()
        request_id = ctx.get("request_id")
        if isinstance(request_id, str) and request_id.strip() != "":
            headers["X-Request-Id"] = request_id
        project_id = ctx.get("project_id")
        if isinstance(project_id, str) and project_id.strip() != "":
            headers["X-Project-Id"] = project_id
        if self._config.signature_secret is not None and self._config.signature_secret.strip() != "":
            ts = str(int(self._now_fn()))
            headers["X-Hook-Timestamp"] = ts
            headers["X-Hook-Signature"] = compute_signature(self._config.signature_secret, ts, body_bytes)
        return headers

    def _post(self, action: str, payload: dict[str, str]) -> HookResponse:
        request_obj = HookRequest(action=action, payload=payload).model_dump(mode="json")
        body_bytes = json.dumps(request_obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
        headers = self._build_headers(body_bytes)

        attempts = self._config.max_retries + 1
        for attempt in range(attempts):
            try:
                resp = self._client.post(self._config.url, content=body_bytes, headers=headers)
                if 500 <= resp.status_code <= 599:
                    raise httpx.HTTPStatusError("Hook server error", request=resp.request, response=resp)
                resp.raise_for_status()
                return HookResponse.model_validate(resp.json())
            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
                is_last = attempt >= attempts - 1
                self._logger.warning(
                    "purchases.hook.error",
                    action=action,
                    attempt=attempt + 1,
                    attempts=attempts,
                    error=str(exc),
                )
                if is_last:
                    break
                backoff_seconds = 0.2 * (2**attempt)
                time.sleep(backoff_seconds)
            except (ValueError, TypeError) as exc:
                self._logger.warning("purchases.hook.invalid_response", action=action, error=str(exc))
                break

        return HookResponse(ok=False, error_code="hook_unavailable", error_message="hook request failed")

    def get_order(self, order_id: str) -> Order | None:
        """Return an order by id, or None if not found."""
        data = self._post("get_order", {"order_id": order_id})
        if not data.ok and data.error_code == "hook_unavailable":
            raise ExternalHookPurchasesAdapter.HookUnavailableError("purchases hook unavailable")
        if not data.ok or data.order is None:
            return None
        return data.order.to_domain()

    def list_orders(self, customer_id: str) -> list[Order]:
        """Return orders for the given customer id."""
        data = self._post("list_orders", {"customer_id": customer_id})
        if not data.ok and data.error_code == "hook_unavailable":
            raise ExternalHookPurchasesAdapter.HookUnavailableError("purchases hook unavailable")
        if not data.ok or data.orders is None:
            return []
        return [o.to_domain() for o in data.orders]

    def get_shipment_by_order_id(self, order_id: str) -> Shipment | None:
        """Return shipment for an order, or None if not found."""
        data = self._post("get_shipment_by_order_id", {"order_id": order_id})
        if not data.ok and data.error_code == "hook_unavailable":
            raise ExternalHookPurchasesAdapter.HookUnavailableError("purchases hook unavailable")
        if not data.ok or data.shipment is None:
            return None
        return data.shipment.to_domain()

    def get_shipment_by_tracking_id(self, tracking_id: str) -> Shipment | None:
        """Return shipment by tracking id, or None if not found."""
        data = self._post("get_shipment_by_tracking_id", {"tracking_id": tracking_id})
        if not data.ok and data.error_code == "hook_unavailable":
            raise ExternalHookPurchasesAdapter.HookUnavailableError("purchases hook unavailable")
        if not data.ok or data.shipment is None:
            return None
        return data.shipment.to_domain()


