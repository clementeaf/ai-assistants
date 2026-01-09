from __future__ import annotations


class APIError(Exception):
    """Base exception for API-related errors."""

    pass


class AuthenticationError(APIError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message)


class RateLimitError(APIError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded") -> None:
        super().__init__(message)


class ValidationError(APIError):
    """Raised when request validation fails."""

    def __init__(self, message: str = "Validation failed", field: str | None = None) -> None:
        super().__init__(message)
        self.field = field
