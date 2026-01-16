"""SQLite backend implementation for calendar storage."""

from __future__ import annotations

import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .base import CalendarBackend


class SQLiteBackend(CalendarBackend):
    """SQLite-based calendar backend."""

    def __init__(self, db_path: str | Path) -> None:
        """
        Initialize SQLite backend.
        @param db_path - Path to SQLite database file
        """
        self._db_path = Path(db_path)
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
                CREATE TABLE IF NOT EXISTS bookings (
                    booking_id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    customer_name TEXT NOT NULL,
                    date_iso TEXT NOT NULL,
                    start_time_iso TEXT NOT NULL,
                    end_time_iso TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'confirmed',
                    created_at TEXT NOT NULL,
                    confirmation_email_sent INTEGER NOT NULL DEFAULT 0,
                    reminder_sent INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_bookings_customer_id ON bookings(customer_id)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_bookings_date ON bookings(date_iso)
                """
            )

    def _get_default_slots(self, date_iso: str) -> list[dict[str, Any]]:
        """Generate default available slots for a date."""
        slots = []
        for hour in range(9, 18):
            start = f"{date_iso}T{hour:02d}:00:00Z"
            end = f"{date_iso}T{hour + 1:02d}:00:00Z"
            slots.append(
                {
                    "date_iso": date_iso,
                    "start_time_iso": start,
                    "end_time_iso": end,
                    "available": True,
                }
            )
        return slots

    def check_availability(self, date_iso: str, start_time_iso: str, end_time_iso: str) -> bool:
        """Check if a time slot is available for booking."""
        with self._get_db() as conn:
            cursor = conn.execute(
                """
                SELECT COUNT(*) as count FROM bookings
                WHERE date_iso = ? 
                AND start_time_iso = ?
                AND end_time_iso = ?
                AND status IN ('pending', 'confirmed')
                """,
                (date_iso, start_time_iso, end_time_iso),
            )
            count = cursor.fetchone()["count"]
            return count == 0

    def get_available_slots(self, date_iso: str) -> list[dict[str, Any]]:
        """Get available slots for a date."""
        default_slots = self._get_default_slots(date_iso)
        with self._get_db() as conn:
            cursor = conn.execute(
                """
                SELECT start_time_iso, end_time_iso FROM bookings
                WHERE date_iso = ?
                AND status IN ('pending', 'confirmed')
                """,
                (date_iso,),
            )
            booked_slots = {(row["start_time_iso"], row["end_time_iso"]) for row in cursor.fetchall()}

        available_slots = []
        for slot in default_slots:
            if (slot["start_time_iso"], slot["end_time_iso"]) not in booked_slots:
                available_slots.append(slot)

        return available_slots

    def create_booking(
        self,
        customer_id: str,
        customer_name: str,
        date_iso: str,
        start_time_iso: str,
        end_time_iso: str,
    ) -> dict[str, Any]:
        """Create a new booking."""
        booking_id = f"BOOKING-{uuid.uuid4().hex[:8].upper()}"
        created_at = datetime.now(tz=timezone.utc).isoformat()

        with self._get_db() as conn:
            conn.execute(
                """
                INSERT INTO bookings (
                    booking_id, customer_id, customer_name, date_iso,
                    start_time_iso, end_time_iso, status, created_at,
                    confirmation_email_sent, reminder_sent
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (booking_id, customer_id, customer_name, date_iso, start_time_iso, end_time_iso, "confirmed", created_at, 0, 0),
            )

        return {
            "booking": {
                "booking_id": booking_id,
                "customer_id": customer_id,
                "customer_name": customer_name,
                "date_iso": date_iso,
                "start_time_iso": start_time_iso,
                "end_time_iso": end_time_iso,
                "status": "confirmed",
                "created_at": created_at,
                "confirmation_email_sent": False,
                "reminder_sent": False,
            }
        }

    def get_booking(self, booking_id: str) -> dict[str, Any] | None:
        """Get a booking by ID."""
        with self._get_db() as conn:
            cursor = conn.execute("SELECT * FROM bookings WHERE booking_id = ?", (booking_id,))
            row = cursor.fetchone()
            if row is None:
                return None

            return {
                "booking": {
                    "booking_id": row["booking_id"],
                    "customer_id": row["customer_id"],
                    "customer_name": row["customer_name"],
                    "date_iso": row["date_iso"],
                    "start_time_iso": row["start_time_iso"],
                    "end_time_iso": row["end_time_iso"],
                    "status": row["status"],
                    "created_at": row["created_at"],
                    "confirmation_email_sent": bool(row["confirmation_email_sent"]),
                    "reminder_sent": bool(row["reminder_sent"]),
                }
            }

    def list_bookings(self, customer_id: str) -> list[dict[str, Any]]:
        """List bookings for a customer."""
        with self._get_db() as conn:
            cursor = conn.execute(
                "SELECT * FROM bookings WHERE customer_id = ? ORDER BY created_at DESC",
                (customer_id,),
            )
            rows = cursor.fetchall()

        bookings = []
        for row in rows:
            bookings.append(
                {
                    "booking_id": row["booking_id"],
                    "customer_id": row["customer_id"],
                    "customer_name": row["customer_name"],
                    "date_iso": row["date_iso"],
                    "start_time_iso": row["start_time_iso"],
                    "end_time_iso": row["end_time_iso"],
                    "status": row["status"],
                    "created_at": row["created_at"],
                    "confirmation_email_sent": bool(row["confirmation_email_sent"]),
                    "reminder_sent": bool(row["reminder_sent"]),
                }
            )

        return {"bookings": bookings}

    def update_booking(
        self,
        booking_id: str,
        date_iso: str | None = None,
        start_time_iso: str | None = None,
        end_time_iso: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any] | None:
        """Update an existing booking."""
        with self._get_db() as conn:
            cursor = conn.execute("SELECT * FROM bookings WHERE booking_id = ?", (booking_id,))
            row = cursor.fetchone()
            if row is None:
                return None

            updates = []
            params = []
            if date_iso is not None:
                updates.append("date_iso = ?")
                params.append(date_iso)
            if start_time_iso is not None:
                updates.append("start_time_iso = ?")
                params.append(start_time_iso)
            if end_time_iso is not None:
                updates.append("end_time_iso = ?")
                params.append(end_time_iso)
            if status is not None:
                updates.append("status = ?")
                params.append(status)

            if updates:
                params.append(booking_id)
                conn.execute(
                    f"UPDATE bookings SET {', '.join(updates)} WHERE booking_id = ?",
                    params,
                )

            cursor = conn.execute("SELECT * FROM bookings WHERE booking_id = ?", (booking_id,))
            row = cursor.fetchone()

            return {
                "booking": {
                    "booking_id": row["booking_id"],
                    "customer_id": row["customer_id"],
                    "customer_name": row["customer_name"],
                    "date_iso": row["date_iso"],
                    "start_time_iso": row["start_time_iso"],
                    "end_time_iso": row["end_time_iso"],
                    "status": row["status"],
                    "created_at": row["created_at"],
                    "confirmation_email_sent": bool(row["confirmation_email_sent"]),
                    "reminder_sent": bool(row["reminder_sent"]),
                }
            }

    def delete_booking(self, booking_id: str) -> bool:
        """Delete a booking."""
        with self._get_db() as conn:
            cursor = conn.execute("DELETE FROM bookings WHERE booking_id = ?", (booking_id,))
            return cursor.rowcount > 0
