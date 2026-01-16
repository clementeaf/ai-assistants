"""OAuth2 handler for Google Calendar integration."""

from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from token_store import TokenStore

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class OAuth2Handler:
    """Handler for Google Calendar OAuth2 flow."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        token_store: TokenStore,
    ) -> None:
        """
        Initialize OAuth2 handler.
        @param client_id - Google OAuth2 client ID
        @param client_secret - Google OAuth2 client secret
        @param redirect_uri - OAuth2 redirect URI
        @param token_store - Token store instance
        """
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._token_store = token_store
        self._state_store: dict[str, str] = {}  # In-memory state store (could be moved to DB)

    def get_authorization_url(self, customer_id: str) -> dict[str, str]:
        """
        Generate authorization URL for a customer.
        @param customer_id - Customer identifier
        @returns Dictionary with authorization_url and state
        """
        state = f"{customer_id}-{secrets.token_urlsafe(32)}"
        self._state_store[state] = customer_id

        # Google agrega scopes adicionales automáticamente (openid, userinfo, etc.)
        # Incluimos estos scopes desde el inicio para evitar el error "Scope has changed"
        extended_scopes = SCOPES + [
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
        ]

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self._redirect_uri],
                }
            },
            scopes=extended_scopes,
        )
        flow.redirect_uri = self._redirect_uri

        authorization_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            state=state,
            prompt="consent",
        )

        return {
            "authorization_url": authorization_url,
            "state": state,
        }

    def handle_callback(self, code: str, state: str) -> dict[str, Any]:
        """
        Handle OAuth2 callback and exchange code for tokens.
        @param code - Authorization code from Google
        @param state - State parameter (contains customer_id)
        @returns Dictionary with success status and customer_id
        """
        customer_id = self._state_store.get(state)
        if not customer_id:
            raise ValueError("Invalid state parameter")

        # Google agrega scopes adicionales automáticamente (openid, userinfo, etc.)
        # Incluimos estos scopes desde el inicio para evitar el error "Scope has changed"
        extended_scopes = SCOPES + [
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
        ]
        
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self._redirect_uri],
                }
            },
            scopes=extended_scopes,
        )
        flow.redirect_uri = self._redirect_uri

        flow.fetch_token(code=code)

        credentials = flow.credentials

        if not credentials.refresh_token:
            raise ValueError("No refresh token received. User may need to re-authorize.")

        token_expiry = datetime.now(tz=timezone.utc) + timedelta(seconds=credentials.expiry.timestamp() if credentials.expiry else 3600)

        calendar_email = None
        try:
            from googleapiclient.discovery import build
            service = build("calendar", "v3", credentials=credentials)
            calendar = service.calendars().get(calendarId="primary").execute()
            calendar_email = calendar.get("id")
        except Exception:
            pass

        self._token_store.store_tokens(
            customer_id=customer_id,
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            token_expiry=token_expiry,
            calendar_email=calendar_email,
        )

        del self._state_store[state]

        return {
            "success": True,
            "customer_id": customer_id,
            "calendar_email": calendar_email,
            "message": "Google Calendar conectado exitosamente",
        }

    def get_credentials(self, customer_id: str) -> Credentials | None:
        """
        Get valid credentials for a customer, refreshing if necessary.
        @param customer_id - Customer identifier
        @returns Credentials object or None if not found
        """
        tokens = self._token_store.get_tokens(customer_id)
        if tokens is None:
            return None

        # Usar los mismos scopes que se usaron al guardar los tokens
        # (incluye openid, userinfo.email, userinfo.profile que Google agrega automáticamente)
        extended_scopes = SCOPES + [
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
        ]

        credentials = Credentials(
            token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self._client_id,
            client_secret=self._client_secret,
            scopes=extended_scopes,
        )

        try:
            # Siempre intentar refrescar si está expirado o si no tiene expiry (token nuevo)
            if credentials.expired or credentials.expiry is None:
                print(f"[OAuth2Handler] Refreshing token for {customer_id} (expired={credentials.expired}, expiry={credentials.expiry})")
                credentials.refresh(Request())
                token_expiry = datetime.now(tz=timezone.utc) + timedelta(seconds=credentials.expiry.timestamp() if credentials.expiry else 3600)
                self._token_store.store_tokens(
                    customer_id=customer_id,
                    access_token=credentials.token,
                    refresh_token=credentials.refresh_token,
                    token_expiry=token_expiry,
                    calendar_email=tokens.get("calendar_email"),
                )
                print(f"[OAuth2Handler] Token refreshed successfully for {customer_id}")
        except Exception as e:
            # Si el refresh falla, puede ser que el refresh_token sea inválido
            # En este caso, retornar None para que el backend maneje el error
            print(f"[OAuth2Handler] Error refreshing token for {customer_id}: {e}")
            print(f"[OAuth2Handler] Token details: has_token={bool(credentials.token)}, has_refresh={bool(credentials.refresh_token)}, scopes={credentials.scopes}")
            raise ValueError(f"Failed to refresh token: {str(e)}")

        return credentials

    def get_connection_status(self, customer_id: str) -> dict[str, Any]:
        """
        Get connection status for a customer.
        @param customer_id - Customer identifier
        @returns Status dictionary
        """
        tokens = self._token_store.get_tokens(customer_id)
        if tokens is None:
            return {
                "connected": False,
                "customer_id": customer_id,
            }

        is_expired = tokens["token_expiry"] < datetime.now(tz=timezone.utc)

        return {
            "connected": not is_expired,
            "customer_id": customer_id,
            "calendar_email": tokens.get("calendar_email"),
            "expires_at": tokens["token_expiry"].isoformat(),
            "needs_refresh": is_expired,
        }

    def disconnect(self, customer_id: str) -> dict[str, Any]:
        """
        Disconnect Google Calendar for a customer.
        @param customer_id - Customer identifier
        @returns Success status
        """
        deleted = self._token_store.delete_tokens(customer_id)
        return {
            "success": deleted,
            "customer_id": customer_id,
            "message": "Google Calendar desconectado" if deleted else "No se encontró conexión",
        }
