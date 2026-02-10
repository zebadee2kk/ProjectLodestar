"""Tests for OrchestratorEngine — end-to-end integration."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from modules.orchestrator.core import OrchestratorEngine
from modules.orchestrator.synthesizer import SynthesisResult
from modules.orchestrator.tools.base import ToolResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_playbook(tmp_dir: Path, name: str, content: dict) -> None:
    (tmp_dir / f"{name}.yaml").write_text(yaml.dump(content))


def _make_proxy():
    proxy = MagicMock()
    proxy.event_bus = MagicMock()
    proxy.handle_request.return_value = {
        "task": "general",
        "model": "gpt-3.5-turbo",
        "result": MagicMock(success=True, response="LLM output"),
        "cost_entry": {"cost": 0.0, "savings": 0.0},
    }
    return proxy


def _make_engine(tmp_dir, proxy=None):
    pb_dir = tmp_dir / "playbooks"
    pb_dir.mkdir(exist_ok=True)
    db_path = str(tmp_dir / "test_runs.db")
    config = {
        "enabled": True,
        "playbooks_dir": str(pb_dir),
        "db_path": db_path,
        "output_dir": str(tmp_dir),
    }
    engine = OrchestratorEngine(config, proxy=proxy or _make_proxy())
    engine.start()
    return engine, pb_dir


# ---------------------------------------------------------------------------
# health_check
# ---------------------------------------------------------------------------

class TestHealthCheck:
    def test_healthy_when_enabled(self, tmp_path):
        engine, _ = _make_engine(tmp_path)
        health = engine.health_check()
        assert health["status"] == "healthy"
        assert health["enabled"] is True

    def test_down_when_disabled(self, tmp_path):
        proxy = _make_proxy()
        config = {"enabled": False, "playbooks_dir": str(tmp_path), "db_path": str(tmp_path / "db.db")}
        engine = OrchestratorEngine(config, proxy=proxy)
        engine.start()
        assert engine.health_check()["status"] == "down"

    def test_lists_available_playbooks(self, tmp_path):
        engine, pb_dir = _make_engine(tmp_path)
        _write_playbook(pb_dir, "my_pb", {"name": "my_pb", "steps": []})
        # Reload (cache is per-instance but list reads directory)
        health = engine.health_check()
        assert "my_pb" in health["playbook_names"]


# ---------------------------------------------------------------------------
# list_playbooks
# ---------------------------------------------------------------------------

class TestListPlaybooks:
    def test_empty_initially(self, tmp_path):
        engine, _ = _make_engine(tmp_path)
        assert engine.list_playbooks() == []

    def test_returns_playbook_names(self, tmp_path):
        engine, pb_dir = _make_engine(tmp_path)
        _write_playbook(pb_dir, "alpha", {"name": "alpha", "steps": []})
        _write_playbook(pb_dir, "beta", {"name": "beta", "steps": []})
        names = engine.list_playbooks()
        assert "alpha" in names
        assert "beta" in names


# ---------------------------------------------------------------------------
# run — fallback (no playbook)
# ---------------------------------------------------------------------------

class TestRunFallback:
    def test_single_llm_step_executed(self, tmp_path):
        engine, _ = _make_engine(tmp_path)
        result = engine.run("Do something useful")
        assert isinstance(result, SynthesisResult)
        assert result.step_count >= 1

    def test_success_with_working_proxy(self, tmp_path):
        engine, _ = _make_engine(tmp_path)
        result = engine.run("Hello LLM")
        assert result.success

    def test_cost_tracked(self, tmp_path):
        engine, _ = _make_engine(tmp_path)
        result = engine.run("test cost tracking")
        assert result.total_cost >= 0.0

    def test_history_recorded(self, tmp_path):
        engine, _ = _make_engine(tmp_path)
        engine.run("record this run")
        history = engine.history(limit=5)
        assert len(history) >= 1
        assert history[0]["status"] in ("completed", "failed")


# ---------------------------------------------------------------------------
# run — with a playbook
# ---------------------------------------------------------------------------

class TestRunWithPlaybook:
    def test_playbook_steps_executed(self, tmp_path):
        engine, pb_dir = _make_engine(tmp_path)
        _write_playbook(pb_dir, "simple", {
            "name": "simple",
            "description": "simple test",
            "steps": [
                {"name": "gen_code", "tool_type": "llm", "capability": "code_generation",
                 "prompt": "Write hello world in Python"},
            ],
        })
        result = engine.run("write hello world", playbook_name="simple")
        assert result.step_count >= 1

    def test_file_steps_write_artifacts(self, tmp_path):
        engine, pb_dir = _make_engine(tmp_path)
        _write_playbook(pb_dir, "write_test", {
            "name": "write_test",
            "description": "write a file",
            "steps": [
                {"name": "write_file", "tool_type": "file", "capability": "file_write",
                 "operation": "write", "path": "output.txt", "content": "hello artifact"},
            ],
        })
        result = engine.run("write a file", playbook_name="write_test")
        output_path = tmp_path / "output.txt"
        assert output_path.exists()
        assert output_path.read_text() == "hello artifact"

    def test_dependency_resolution_in_playbook(self, tmp_path):
        engine, pb_dir = _make_engine(tmp_path)
        _write_playbook(pb_dir, "chained", {
            "name": "chained",
            "description": "chained steps",
            "steps": [
                {"name": "first", "tool_type": "llm", "capability": "general",
                 "prompt": "first step"},
                {"name": "second", "tool_type": "llm", "capability": "general",
                 "prompt": "second step", "depends_on": ["first"]},
            ],
        })
        result = engine.run("chain test", playbook_name="chained")
        # Both should complete
        assert result.step_count == 2

    def test_progress_callback_called(self, tmp_path):
        engine, pb_dir = _make_engine(tmp_path)
        _write_playbook(pb_dir, "progress", {
            "name": "progress",
            "description": "progress test",
            "steps": [
                {"name": "s1", "tool_type": "llm", "capability": "general", "prompt": "p1"},
                {"name": "s2", "tool_type": "llm", "capability": "general", "prompt": "p2"},
            ],
        })
        calls = []
        result = engine.run(
            "progress test",
            playbook_name="progress",
            progress_callback=lambda name, i, t: calls.append(name),
        )
        assert "s1" in calls
        assert "s2" in calls

    def test_variables_substituted(self, tmp_path):
        engine, pb_dir = _make_engine(tmp_path)
        _write_playbook(pb_dir, "vars", {
            "name": "vars",
            "description": "variable substitution test",
            "steps": [
                {"name": "gen", "tool_type": "llm", "capability": "general",
                 "prompt": "For database: {db_type}"},
            ],
        })
        engine.run("test vars", playbook_name="vars", variables={"db_type": "PostgreSQL"})
        # Verify the substituted prompt reached the proxy
        proxy = engine.proxy
        call_args = proxy.handle_request.call_args
        # The prompt kwarg or first positional arg should contain "PostgreSQL"
        prompt_sent = call_args[1].get("prompt") or call_args[0][0]
        assert "PostgreSQL" in prompt_sent


# ---------------------------------------------------------------------------
# history
# ---------------------------------------------------------------------------

class TestHistory:
    def test_empty_history(self, tmp_path):
        engine, _ = _make_engine(tmp_path)
        assert engine.history() == []

    def test_history_grows_with_runs(self, tmp_path):
        engine, _ = _make_engine(tmp_path)
        engine.run("first run")
        engine.run("second run")
        history = engine.history(limit=10)
        assert len(history) == 2

    def test_history_entry_structure(self, tmp_path):
        engine, _ = _make_engine(tmp_path)
        engine.run("structure test")
        entry = engine.history()[0]
        assert "run_id" in entry
        assert "status" in entry
        assert "cost" in entry
        assert "steps" in entry
        assert "request" in entry


# ---------------------------------------------------------------------------
# register_tool
# ---------------------------------------------------------------------------

class TestRegisterTool:
    def test_custom_tool_used(self, tmp_path):
        engine, pb_dir = _make_engine(tmp_path)
        _write_playbook(pb_dir, "custom", {
            "name": "custom",
            "description": "custom tool test",
            "steps": [
                {"name": "s1", "tool_type": "custom_type", "capability": "custom_cap",
                 "prompt": "custom"},
            ],
        })

        custom_tool = MagicMock()
        custom_tool.can_handle.return_value = True
        custom_tool.estimate_cost.return_value = 0.0
        custom_tool.execute.return_value = ToolResult(
            success=True, output="custom_out", artifacts={"s1": "custom_out"}
        )
        engine.register_tool(custom_tool)

        result = engine.run("custom test", playbook_name="custom")
        assert custom_tool.execute.called
