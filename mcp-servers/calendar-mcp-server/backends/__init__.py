"""Backend implementations for calendar storage."""

from calendar_mcp_server.backends.base import CalendarBackend
from calendar_mcp_server.backends.sqlite_backend import SQLiteBackend

try:
    from calendar_mcp_server.backends.google_calendar_backend import GoogleCalendarBackend
    __all__ = ["CalendarBackend", "SQLiteBackend", "GoogleCalendarBackend"]
except ImportError:
    __all__ = ["CalendarBackend", "SQLiteBackend"]
