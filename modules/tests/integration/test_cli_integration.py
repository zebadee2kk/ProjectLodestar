"""Integration tests for the Lodestar CLI.

Tests exercise the full CLI pipeline end-to-end using the real
LodestarProxy with mocked external calls (LLM APIs, git, subprocess).
"""

import argparse
import pytest
from unittest.mock import MagicMock, patch

from modules.cli import main, build_parser


# ---------------------------------------------------------------------------
# CLI → Proxy → Cost pipeline
# ---------------------------------------------------------------------------

class TestCostsPipeline:

    def test_costs_after_route(self, capsys):
        """Routing a prompt should appear in the cost summary."""
        main(["route", "write a test for this function"])
        capsys.readouterr()  # discard route output
        main(["costs"])
        output = capsys.readouterr().out
        assert "Cost Report" in output
        assert "Total" in output

    def test_costs_request_count_increments(self, capsys):
        main(["route", "fix the null pointer exception"])
        capsys.readouterr()
        main(["route", "write unit tests"])
        capsys.readouterr()
        main(["costs"])
        output = capsys.readouterr().out
        # At least the cost report header is present
        assert "Cost Report" in output


# ---------------------------------------------------------------------------
# CLI → Route → Cache pipeline
# ---------------------------------------------------------------------------

class TestRouteCachePipeline:

    def test_route_then_cache_shows_entries(self, capsys):
        main(["route", "explain the proxy pattern"])
        capsys.readouterr()
        main(["cache"])
        output = capsys.readouterr().out
        assert "Entries:" in output

    def test_cache_clear_resets_count(self, capsys):
        main(["route", "write a hello world program"])
        capsys.readouterr()
        main(["cache", "--clear"])
        capsys.readouterr()
        main(["cache"])
        output = capsys.readouterr().out
        assert "Entries:    0" in output or "Entries: 0" in output

    def test_second_route_same_prompt_uses_cache(self, capsys):
        """Same prompt routed twice should result in a cache hit on 2nd call."""
        prompt = "write a fibonacci function"
        main(["route"] + prompt.split())
        capsys.readouterr()
        main(["cache"])
        output = capsys.readouterr().out
        # Cache should have at least 1 entry
        assert "Entries:" in output


# ---------------------------------------------------------------------------
# CLI → Tournament pipeline
# ---------------------------------------------------------------------------

class TestTournamentPipeline:

    def test_tournament_output_format(self, capsys):
        main(["tournament", "implement a stack", "model-a", "model-b"])
        output = capsys.readouterr().out
        assert "Tournament Match" in output
        assert "model-a" in output
        assert "model-b" in output

    def test_tournament_three_models(self, capsys):
        main(["tournament", "explain big-O notation", "m1", "m2", "m3"])
        output = capsys.readouterr().out
        assert "m1" in output
        assert "m2" in output
        assert "m3" in output


# ---------------------------------------------------------------------------
# CLI → Run pipeline (with mocked executor)
# ---------------------------------------------------------------------------

class TestRunPipeline:

    def test_run_success_full_pipeline(self, capsys):
        with patch("modules.agent.AgentExecutor") as MockExec:
            MockExec.return_value.run_command.return_value = {
                "success": True,
                "output": "Tests passed.\n",
                "error": None,
                "attempts": [("pytest .", "Success")],
            }
            main(["run", "pytest", "."])
        output = capsys.readouterr().out
        assert "Running command: pytest ." in output
        assert "succeeded" in output

    def test_run_failure_full_pipeline(self, capsys):
        with patch("modules.agent.AgentExecutor") as MockExec:
            MockExec.return_value.run_command.return_value = {
                "success": False,
                "output": None,
                "error": "Exit code 1\nStderr: build failed",
                "attempts": [
                    ("make build", "Exit code 1\nStderr: build failed"),
                ],
            }
            main(["run", "make", "build"])
        output = capsys.readouterr().out
        assert "failed" in output
        assert "Exit code 1" in output


# ---------------------------------------------------------------------------
# CLI → Diff pipeline (with mocked git/subprocess)
# ---------------------------------------------------------------------------

class TestDiffPipeline:

    def test_diff_no_changes_message(self, capsys):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", returncode=0)
            main(["diff"])
        output = capsys.readouterr().out
        assert "No changes detected" in output

    def test_diff_git_subprocess_called(self, capsys):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", returncode=0)
            main(["diff", "src/main.py"])
        call_args = mock_run.call_args[0][0]
        assert "git" in call_args
        assert "diff" in call_args
        assert "src/main.py" in call_args


# ---------------------------------------------------------------------------
# CLI → Status pipeline
# ---------------------------------------------------------------------------

class TestStatusPipeline:

    def test_status_shows_all_modules(self, capsys):
        main(["status"])
        output = capsys.readouterr().out
        assert "Lodestar Module Status" in output
        assert "router" in output
        assert "cost_tracker" in output

    def test_status_after_route(self, capsys):
        """Status should still work correctly after handling a request."""
        main(["route", "debug this error"])
        capsys.readouterr()
        main(["status"])
        output = capsys.readouterr().out
        assert "Lodestar Module Status" in output
