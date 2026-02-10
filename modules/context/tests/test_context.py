"""Tests for the Context module."""

import pytest
import os
from modules.context.session import SessionManager


class TestSessionManager:
    @pytest.fixture
    def manager(self, tmp_path):
        db_file = tmp_path / "test_sessions.db"
        return SessionManager({"db_path": str(db_file)})

    def test_create_session(self, manager):
        sid = manager.create_session("Test Session", {"key": "val"})
        assert isinstance(sid, str)
        
        session = manager.get_session(sid)
        assert session["name"] == "Test Session"
        assert session["metadata"]["key"] == "val"

    def test_history(self, manager):
        sid = manager.create_session("History Test")
        manager.append_history(sid, "user", "hello")
        manager.append_history(sid, "assistant", "hi there")
        
        history = manager.get_history(sid)
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"
        assert history[1]["content"] == "hi there"

    def test_list_sessions(self, manager):
        manager.create_session("S1")
        manager.create_session("S2")
        sessions = manager.list_sessions()
        assert len(sessions) == 2
        assert sessions[0]["name"] == "S2"  # Ordered by updated_at desc
