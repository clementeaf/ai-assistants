"""Token storage for OAuth2 credentials per user."""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet


class TokenStore:
    """Secure token storage for OAuth2 credentials."""

    def __init__(self, db_path: str | Path, encryption_key: str | None = None) -> None:
        """
        Initialize token store.
        @param db_path - Path to SQLite database
        @param encryption_key - Encryption key for tokens (if None, tokens stored in plain text - NOT RECOMMENDED)
        """
        self._db_path = Path(db_path)
        self._cipher = None
        
        if encryption_key:
            try:
                key = encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
                if len(key) != 32:
                    key = Fernet.generate_key()
                self._cipher = Fernet(key)
            except Exception:
                self._cipher = None
        
        self._init_db()

    @contextmanager
    def _get_db(self):
        """Get database connection with automatic commit/rollback."""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with self._get_db() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS oauth_tokens (
                    customer_id TEXT PRIMARY KEY,
                    access_token TEXT NOT NULL,
                    refresh_token TEXT NOT NULL,
                    token_expiry TEXT NOT NULL,
                    calendar_email TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_oauth_tokens_customer_id 
                ON oauth_tokens(customer_id)
                """
            )

    def _encrypt(self, data: str) -> str:
        """
        Encrypt data if cipher is available.
        @param data - Data to encrypt
        @returns Encrypted data or original if no cipher
        """
        if self._cipher and data:
            return self._cipher.encrypt(data.encode()).decode()
        return data

    def _decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt data if cipher is available.
        @param encrypted_data - Encrypted data
        @returns Decrypted data or original if no cipher
        """
        if self._cipher and encrypted_data:
            try:
                return self._cipher.decrypt(encrypted_data.encode()).decode()
            except Exception:
                return encrypted_data
        return encrypted_data

    def store_tokens(
        self,
        customer_id: str,
        access_token: str,
        refresh_token: str,
        token_expiry: datetime,
        calendar_email: str | None = None,
    ) -> None:
        """
        Store OAuth2 tokens for a customer.
        @param customer_id - Customer identifier
        @param access_token - OAuth2 access token
        @param refresh_token - OAuth2 refresh token
        @param token_expiry - Token expiration datetime
        @param calendar_email - Email of the connected calendar (optional)
        """
        now = datetime.now(tz=timezone.utc).isoformat()
        encrypted_access = self._encrypt(access_token)
        encrypted_refresh = self._encrypt(refresh_token)

        with self._get_db() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO oauth_tokens (
                    customer_id, access_token, refresh_token, token_expiry,
                    calendar_email, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, 
                    COALESCE((SELECT created_at FROM oauth_tokens WHERE customer_id = ?), ?),
                    ?
                )
                """,
                (
                    customer_id,
                    encrypted_access,
                    encrypted_refresh,
                    token_expiry.isoformat(),
                    calendar_email,
                    customer_id,
                    now,
                    now,
                ),
            )

    def get_tokens(self, customer_id: str) -> dict[str, Any] | None:
        """
        Get OAuth2 tokens for a customer.
        @param customer_id - Customer identifier
        @returns Token dictionary or None if not found
        """
        with self._get_db() as conn:
            cursor = conn.execute(
                "SELECT * FROM oauth_tokens WHERE customer_id = ?",
                (customer_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None

            return {
                "customer_id": row["customer_id"],
                "access_token": self._decrypt(row["access_token"]),
                "refresh_token": self._decrypt(row["refresh_token"]),
                "token_expiry": datetime.fromisoformat(row["token_expiry"]),
                "calendar_email": row["calendar_email"],
                "created_at": datetime.fromisoformat(row["created_at"]),
                "updated_at": datetime.fromisoformat(row["updated_at"]),
            }

    def delete_tokens(self, customer_id: str) -> bool:
        """
        Delete OAuth2 tokens for a customer.
        @param customer_id - Customer identifier
        @returns True if deleted, False if not found
        """
        with self._get_db() as conn:
            cursor = conn.execute(
                "DELETE FROM oauth_tokens WHERE customer_id = ?",
                (customer_id,),
            )
            return cursor.rowcount > 0

    def is_connected(self, customer_id: str) -> bool:
        """
        Check if a customer has Google Calendar connected.
        @param customer_id - Customer identifier
        @returns True if connected, False otherwise
        """
        tokens = self.get_tokens(customer_id)
        if tokens is None:
            return False
        
        expiry = tokens["token_expiry"]
        if expiry < datetime.now(tz=timezone.utc):
            return False
        
        return True
