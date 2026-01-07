from __future__ import annotations

from pathlib import Path

import pytest

from ai_assistants.adapters.demo_purchases import DemoPurchasesAdapter
from ai_assistants.adapters.registry import set_purchases_adapter
from ai_assistants.orchestrator.runtime import Orchestrator
from ai_assistants.persistence.conversation_store import InMemoryConversationStore
from ai_assistants.persistence.sqlite_memory_store import SqliteCustomerMemoryStore, SqliteMemoryStoreConfig


@pytest.fixture(autouse=True)
def _deterministic_adapter() -> None:
    set_purchases_adapter(DemoPurchasesAdapter())
    yield
    set_purchases_adapter(None)


def test_long_term_memory_persists_last_tracking_across_conversations(tmp_path: Path) -> None:
    memory_path = tmp_path / "mem.sqlite3"
    memory_store = SqliteCustomerMemoryStore(SqliteMemoryStoreConfig(path=memory_path))
    orch = Orchestrator(store=InMemoryConversationStore(), memory_store=memory_store)

    # first conversation stores last_tracking_id into long-term memory
    first = orch.run_turn(
        conversation_id="web:conv-1",
        user_text="Seguimiento de ORDER-200",
        customer_id="+5491112345678",
    )
    assert "TRACK-9002" in first.response_text

    # second conversation can resolve follow-up using long-term memory
    second = orch.run_turn(
        conversation_id="web:conv-2",
        user_text="y el seguimiento?",
        customer_id="+5491112345678",
    )
    assert "TRACK-9002" in second.response_text


