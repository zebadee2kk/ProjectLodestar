"""Shared fixtures for integration tests.

These fixtures provide a fully initialised LodestarProxy backed by
temporary SQLite databases so tests run in isolation without touching
production data.
"""

import os
import tempfile
import pytest

from modules.routing.proxy import LodestarProxy


@pytest.fixture
def temp_db_dir(tmp_path):
    """Provide a temporary directory for SQLite databases."""
    return tmp_path


@pytest.fixture
def proxy(temp_db_dir):
    """Provide a started LodestarProxy backed by temp databases.

    The proxy is started before each test and stopped afterwards.
    All SQLite databases are written to a temp directory so tests
    never pollute the real .lodestar/ directory.
    """
    # Point databases at temp dir
    cache_db = str(temp_db_dir / "cache.db")
    costs_db = str(temp_db_dir / "costs.db")

    p = LodestarProxy()
    # Patch database paths to temp locations
    p.cache.db_path = temp_db_dir / "cache.db"
    p.cost_tracker.storage_path = str(costs_db)

    p.start()
    yield p
    p.stop()


@pytest.fixture
def dry_run_fn():
    """A no-op request function that returns a canned response.

    Use this when you want to exercise the full proxy pipeline
    without making real LLM API calls.
    """
    def _fn(model, prompt_text=None):
        return f"[mock response from {model}]"
    return _fn
