"""Tests for configuration loading."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ai_assistants.config.app_config import AppConfig, load_app_config
from ai_assistants.config.database_config import DatabaseConfig, load_database_config
from ai_assistants.config.security_config import SecurityConfig, load_security_config


def test_load_app_config_defaults() -> None:
    """Test loading app config with defaults."""
    config = load_app_config()
    
    assert isinstance(config, AppConfig)
    assert config.max_messages > 0
    assert config.max_processed_events > 0
    assert config.thread_pool_workers > 0


def test_load_app_config_custom() -> None:
    """Test loading app config with custom values."""
    os.environ["AI_ASSISTANTS_MAX_MESSAGES"] = "100"
    os.environ["AI_ASSISTANTS_MAX_PROCESSED_EVENTS"] = "2000"
    os.environ["AI_ASSISTANTS_THREAD_POOL_WORKERS"] = "8"
    
    try:
        config = load_app_config()
        assert config.max_messages == 100
        assert config.max_processed_events == 2000
        assert config.thread_pool_workers == 8
    finally:
        os.environ.pop("AI_ASSISTANTS_MAX_MESSAGES", None)
        os.environ.pop("AI_ASSISTANTS_MAX_PROCESSED_EVENTS", None)
        os.environ.pop("AI_ASSISTANTS_THREAD_POOL_WORKERS", None)


def test_load_database_config() -> None:
    """Test loading database config."""
    config = load_database_config()
    
    assert isinstance(config, DatabaseConfig)
    assert isinstance(config.conversation_store_path, Path)
    assert isinstance(config.job_store_path, Path)
    assert isinstance(config.memory_store_path, Path)
    assert isinstance(config.vector_store_path, Path)


def test_load_security_config() -> None:
    """Test loading security config."""
    config = load_security_config()
    
    assert isinstance(config, SecurityConfig)
    assert isinstance(config.api_keys, dict)
