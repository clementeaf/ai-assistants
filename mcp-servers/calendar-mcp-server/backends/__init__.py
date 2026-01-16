"""Backend implementations for calendar storage."""

from .base import CalendarBackend
from .sqlite_backend import SQLiteBackend

try:
    from .google_calendar_backend import GoogleCalendarBackend
    __all__ = ["CalendarBackend", "SQLiteBackend", "GoogleCalendarBackend"]
except ImportError:
    __all__ = ["CalendarBackend", "SQLiteBackend"]
