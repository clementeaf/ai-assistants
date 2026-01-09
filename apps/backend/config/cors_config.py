from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CORSConfig:
    """CORS configuration for the API."""

    allowed_origins: list[str]
    allow_credentials: bool
    allowed_methods: list[str]
    allowed_headers: list[str]
    exposed_headers: list[str] | None
    max_age: int


def load_cors_config() -> CORSConfig:
    """Load CORS configuration from environment variables.
    
    Environment variables:
    - AI_ASSISTANTS_CORS_ORIGINS: Comma-separated list of allowed origins
      Example: "https://app.example.com,https://admin.example.com"
    - AI_ASSISTANTS_CORS_ALLOW_CREDENTIALS: "true" or "false" (default: "true")
    - AI_ASSISTANTS_CORS_MAX_AGE: Max age for preflight cache in seconds (default: 3600)
    
    If AI_ASSISTANTS_CORS_ORIGINS is not set, defaults to ["*"] for development.
    """
    origins_raw = os.getenv("AI_ASSISTANTS_CORS_ORIGINS", "").strip()
    
    if origins_raw:
        allowed_origins = [origin.strip() for origin in origins_raw.split(",") if origin.strip()]
    else:
        allowed_origins = ["*"]
    
    allow_credentials_raw = os.getenv("AI_ASSISTANTS_CORS_ALLOW_CREDENTIALS", "true").strip().lower()
    allow_credentials = allow_credentials_raw in {"1", "true", "yes", "on"}
    
    max_age_raw = os.getenv("AI_ASSISTANTS_CORS_MAX_AGE", "3600")
    try:
        max_age = int(max_age_raw)
    except ValueError:
        max_age = 3600
    
    allowed_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]
    allowed_headers = [
        "Content-Type",
        "Authorization",
        "X-API-Key",
        "X-Customer-Id",
        "X-Request-Id",
        "X-Webhook-Timestamp",
        "X-Webhook-Signature",
        "Accept",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
    ]
    exposed_headers = [
        "X-Request-Id",
        "Content-Type",
        "Content-Length",
    ]
    
    return CORSConfig(
        allowed_origins=allowed_origins,
        allow_credentials=allow_credentials,
        allowed_methods=allowed_methods,
        allowed_headers=allowed_headers,
        exposed_headers=exposed_headers,
        max_age=max_age,
    )
