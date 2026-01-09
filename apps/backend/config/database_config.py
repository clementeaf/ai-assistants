from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class DatabaseConfig:
    """Database configuration for all SQLite stores."""

    conversation_store_path: Path
    job_store_path: Path
    memory_store_path: Path
    vector_store_path: Path


def load_database_config() -> DatabaseConfig:
    """Load database configuration from environment variables."""
    base_path = os.getenv("AI_ASSISTANTS_DATA_DIR", ".data")
    base_path_obj = Path(base_path)

    conversation_path = Path(
        os.getenv("AI_ASSISTANTS_SQLITE_PATH", str(base_path_obj / "ai_assistants.sqlite3"))
    )
    job_path = Path(
        os.getenv("AI_ASSISTANTS_JOB_STORE_PATH", str(base_path_obj / "ai_assistants_jobs.sqlite3"))
    )
    memory_path = Path(
        os.getenv("AI_ASSISTANTS_MEMORY_STORE_PATH", str(base_path_obj / "ai_assistants_memory.sqlite3"))
    )
    vector_path = Path(
        os.getenv("AI_ASSISTANTS_VECTOR_STORE_PATH", str(base_path_obj / "ai_assistants_vector.sqlite3"))
    )

    return DatabaseConfig(
        conversation_store_path=conversation_path,
        job_store_path=job_path,
        memory_store_path=memory_path,
        vector_store_path=vector_path,
    )
