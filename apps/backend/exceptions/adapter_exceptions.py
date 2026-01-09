from __future__ import annotations


class AdapterError(Exception):
    """Base exception for adapter-related errors."""

    pass


class AdapterUnavailableError(AdapterError):
    """Raised when an adapter service is unavailable."""

    def __init__(self, message: str = "Adapter service is unavailable", adapter_name: str | None = None) -> None:
        super().__init__(message)
        self.adapter_name = adapter_name


class AdapterTimeoutError(AdapterError):
    """Raised when an adapter operation times out."""

    def __init__(self, message: str = "Adapter operation timed out", timeout_seconds: float | None = None) -> None:
        super().__init__(message)
        self.timeout_seconds = timeout_seconds
