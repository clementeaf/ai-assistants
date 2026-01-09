"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from ai_assistants.adapters.demo_bookings import DemoBookingsAdapter
from ai_assistants.adapters.demo_purchases import DemoPurchasesAdapter
from ai_assistants.adapters.registry import set_bookings_adapter, set_purchases_adapter
from ai_assistants.persistence.sqlite_store import SqliteConversationStore, SqliteStoreConfig
from ai_assistants.persistence.sqlite_memory_store import SqliteCustomerMemoryStore, SqliteMemoryStoreConfig


@pytest.fixture
def temp_db_path() -> Path:
    """Create a temporary database path for testing."""
    with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as f:
        db_path = Path(f.name)
    yield db_path
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def conversation_store(temp_db_path: Path) -> SqliteConversationStore:
    """Create a conversation store for testing."""
    config = SqliteStoreConfig(path=temp_db_path)
    store = SqliteConversationStore(config)
    yield store
    if temp_db_path.exists():
        temp_db_path.unlink()


@pytest.fixture
def memory_store(temp_db_path: Path) -> SqliteCustomerMemoryStore:
    """Create a memory store for testing."""
    config = SqliteMemoryStoreConfig(path=temp_db_path)
    store = SqliteCustomerMemoryStore(config)
    yield store
    if temp_db_path.exists():
        temp_db_path.unlink()


@pytest.fixture
def demo_adapters() -> None:
    """Set up demo adapters for testing."""
    set_bookings_adapter(DemoBookingsAdapter())
    set_purchases_adapter(DemoPurchasesAdapter())
    yield
    set_bookings_adapter(None)
    set_purchases_adapter(None)
