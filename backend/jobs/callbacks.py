from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Final

import httpx
from structlog.contextvars import get_contextvars

from ai_assistants.channels.webhook_security import compute_signature
from ai_assistants.observability.logging import get_logger
from ai_assistants.persistence.job_store import JobRecord

_DEFAULT_TIMEOUT_SECONDS: Final[float] = 5.0


@dataclass(frozen=True, slots=True)
class JobCallbackConfig:
    """Configuration for async job completion callbacks."""

    url: str
    api_key: str | None
    signature_secret: str | None
    timeout_seconds: float
    max_retries: int


def load_job_callback_config() -> JobCallbackConfig | None:
    """Load job callback config from env vars.

    If AI_ASSISTANTS_JOB_CALLBACK_URL is not set, callbacks are disabled.
    """
    url = os.getenv("AI_ASSISTANTS_JOB_CALLBACK_URL")
    if url is None or url.strip() == "":
        return None

    api_key = os.getenv("AI_ASSISTANTS_JOB_CALLBACK_API_KEY")
    signature_secret = os.getenv("AI_ASSISTANTS_JOB_CALLBACK_SIGNATURE_SECRET")

    timeout_raw = os.getenv("AI_ASSISTANTS_JOB_CALLBACK_TIMEOUT_SECONDS", str(_DEFAULT_TIMEOUT_SECONDS))
    try:
        timeout_seconds = float(timeout_raw)
    except ValueError:
        timeout_seconds = _DEFAULT_TIMEOUT_SECONDS

    retries_raw = os.getenv("AI_ASSISTANTS_JOB_CALLBACK_MAX_RETRIES", "2")
    try:
        max_retries = int(retries_raw)
    except ValueError:
        max_retries = 2
    if max_retries < 0:
        max_retries = 0

    return JobCallbackConfig(
        url=url,
        api_key=api_key,
        signature_secret=signature_secret,
        timeout_seconds=timeout_seconds,
        max_retries=max_retries,
    )


class JobCallbackSender:
    """Sends job completion callbacks to an external service."""

    def __init__(self, config: JobCallbackConfig, client: httpx.Client | None = None) -> None:
        self._config = config
        self._client = client or httpx.Client(timeout=config.timeout_seconds)
        self._logger = get_logger()

    def notify(self, record: JobRecord) -> None:
        """Send a callback notification for the given job record."""
        ctx = get_contextvars()
        request_id = ctx.get("request_id")
        project_id = ctx.get("project_id")

        payload = {
            "job_id": record.job_id,
            "status": record.status.value,
            "conversation_id": record.conversation_id,
            "message_id": record.message_id,
            "response_text": record.response_text,
            "error_text": record.error_text,
        }
        body_bytes = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if isinstance(request_id, str) and request_id.strip() != "":
            headers["X-Request-Id"] = request_id
        if isinstance(project_id, str) and project_id.strip() != "":
            headers["X-Project-Id"] = project_id
        if self._config.api_key is not None and self._config.api_key.strip() != "":
            headers["X-API-Key"] = self._config.api_key
        if self._config.signature_secret is not None and self._config.signature_secret.strip() != "":
            ts = str(int(time.time()))
            headers["X-Callback-Timestamp"] = ts
            headers["X-Callback-Signature"] = compute_signature(self._config.signature_secret, ts, body_bytes)

        attempts = self._config.max_retries + 1
        for attempt in range(attempts):
            try:
                resp = self._client.post(self._config.url, content=body_bytes, headers=headers)
                if 500 <= resp.status_code <= 599:
                    raise httpx.HTTPStatusError("Callback server error", request=resp.request, response=resp)
                resp.raise_for_status()
                self._logger.info("job.callback.sent", job_id=record.job_id, status=record.status.value)
                return
            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
                is_last = attempt >= attempts - 1
                self._logger.warning(
                    "job.callback.error",
                    job_id=record.job_id,
                    status=record.status.value,
                    attempt=attempt + 1,
                    attempts=attempts,
                    error=str(exc),
                )
                if is_last:
                    return
                time.sleep(0.2 * (2**attempt))


