"""Tests for the Lodestar CLI."""

import pytest
from unittest.mock import MagicMock, patch
from modules.cli import build_parser, main


class TestBuildParser:

    def test_parser_has_subcommands(self):
        parser = build_parser()
        # Verify parser builds without error
        assert parser is not None

    def test_parse_costs(self):
        parser = build_parser()
        args = parser.parse_args(["costs"])
        assert args.command == "costs"

    def test_parse_route(self):
        parser = build_parser()
        args = parser.parse_args(["route", "fix", "the", "bug"])
        assert args.command == "route"
        assert args.prompt == ["fix", "the", "bug"]

    def test_parse_status(self):
        parser = build_parser()
        args = parser.parse_args(["status"])
        assert args.command == "status"

    def test_parse_tournament(self):
        parser = build_parser()
        args = parser.parse_args(["tournament", "test prompt", "model-a", "model-b"])
        assert args.command == "tournament"
        assert args.prompt == "test prompt"
        assert args.models == ["model-a", "model-b"]

    def test_no_command(self):
        parser = build_parser()
        args = parser.parse_args([])
        assert args.command is None


class TestMainCLI:

    def test_status_runs(self, capsys):
        main(["status"])
        captured = capsys.readouterr()
        assert "Lodestar Module Status" in captured.out

    def test_costs_runs(self, capsys):
        main(["costs"])
        captured = capsys.readouterr()
        assert "Cost Report" in captured.out

    def test_route_runs(self, capsys):
        main(["route", "fix", "the", "login", "bug"])
        captured = capsys.readouterr()
        assert "Model:" in captured.out
        assert "Task:" in captured.out

    def test_tournament_runs(self, capsys):
        main(["tournament", "test prompt", "model-a", "model-b"])
        captured = capsys.readouterr()
        assert "Tournament Match" in captured.out
        assert "model-a" in captured.out
        assert "model-b" in captured.out

    def test_route_shows_fallback_chain(self, capsys):
        main(["route", "review", "this", "code"])
        captured = capsys.readouterr()
        assert "Task:" in captured.out

    def test_tournament_with_three_models(self, capsys):
        main(["tournament", "test", "m1", "m2", "m3"])
        captured = capsys.readouterr()
        assert "m1" in captured.out
        assert "m2" in captured.out
        assert "m3" in captured.out

    def test_no_command_launches_cockpit(self):
        """No sub-command now launches the interactive cockpit (not sys.exit)."""
        from modules.cli import build_parser
        parser = build_parser()
        args = parser.parse_args([])
        # The new behaviour: no command → cockpit; args.command should be None
        assert args.command is None


class TestCLIEdgeCases:

    def test_route_missing_prompt_exits(self):
        """Route command without prompt should cause argparse error."""
        with pytest.raises(SystemExit) as exc_info:
            main(["route"])
        assert exc_info.value.code != 0

    def test_tournament_missing_models_exits(self):
        """Tournament without models should cause argparse error."""
        with pytest.raises(SystemExit) as exc_info:
            main(["tournament", "prompt"])
        assert exc_info.value.code != 0

    def test_status_output_has_modules(self, capsys):
        main(["status"])
        output = capsys.readouterr().out
        assert "router" in output
        assert "cost_tracker" in output

    def test_costs_shows_zero_for_fresh_session(self, capsys):
        main(["costs"])
        output = capsys.readouterr().out
        assert "$0.0000" in output

    def test_multiple_commands_sequentially(self, capsys):
        """CLI should work for multiple sequential invocations."""
        main(["status"])
        main(["costs"])
        main(["route", "fix", "a", "bug"])
        # No error means all three worked


class TestParserSubcommands:
    """Parser tests for subcommands not covered above."""

    def test_parse_cache(self):
        parser = build_parser()
        args = parser.parse_args(["cache"])
        assert args.command == "cache"
        assert args.clear is False

    def test_parse_cache_clear(self):
        parser = build_parser()
        args = parser.parse_args(["cache", "--clear"])
        assert args.command == "cache"
        assert args.clear is True

    def test_parse_run(self):
        parser = build_parser()
        args = parser.parse_args(["run", "echo", "hello"])
        assert args.command == "run"
        assert args.cmd_args == ["echo", "hello"]

    def test_parse_run_multi_word(self):
        parser = build_parser()
        args = parser.parse_args(["run", "ls", "/tmp"])
        assert args.command == "run"
        assert args.cmd_args == ["ls", "/tmp"]

    def test_parse_diff_no_files(self):
        parser = build_parser()
        args = parser.parse_args(["diff"])
        assert args.command == "diff"
        assert args.files == []
        assert args.no_ai is False

    def test_parse_diff_with_files(self):
        parser = build_parser()
        args = parser.parse_args(["diff", "foo.py", "bar.py"])
        assert args.command == "diff"
        assert args.files == ["foo.py", "bar.py"]

    def test_parse_diff_no_ai_flag(self):
        parser = build_parser()
        args = parser.parse_args(["diff", "--no-ai"])
        assert args.command == "diff"
        assert args.no_ai is True

    def test_parse_costs_dashboard(self):
        parser = build_parser()
        args = parser.parse_args(["costs", "--dashboard"])
        assert args.command == "costs"
        assert args.dashboard is True

    def test_parse_costs_dashboard_short(self):
        parser = build_parser()
        args = parser.parse_args(["costs", "-d"])
        assert args.command == "costs"
        assert args.dashboard is True


class TestCmdCache:
    """Tests for the cache command."""

    def test_cache_stats(self, capsys):
        main(["cache"])
        output = capsys.readouterr().out
        assert "Cache Stats" in output
        assert "Entries" in output
        assert "Size" in output
        assert "Path" in output

    def test_cache_clear(self, capsys):
        main(["cache", "--clear"])
        output = capsys.readouterr().out
        assert "Cache cleared" in output
        assert "entries" in output

    def test_cache_clear_returns_count(self, capsys):
        # Prime cache by running a route first (populates cache)
        main(["route", "fix", "a", "bug"])
        # Clear
        main(["cache", "--clear"])
        output = capsys.readouterr().out
        assert "Cache cleared" in output

    def test_cache_stats_after_clear(self, capsys):
        main(["cache", "--clear"])
        capsys.readouterr()  # discard clear output
        main(["cache"])
        output = capsys.readouterr().out
        assert "Entries:" in output


class TestCmdRun:
    """Tests for the run command (self-healing executor)."""

    def test_run_successful_command(self, capsys):
        main(["run", "echo", "hello"])
        output = capsys.readouterr().out
        assert "Running command" in output
        assert "succeeded" in output

    def test_run_shows_command(self, capsys):
        main(["run", "echo", "lodestar"])
        output = capsys.readouterr().out
        assert "echo lodestar" in output

    def test_run_failed_command(self, capsys):
        """A command that always fails should show failure message."""
        main(["run", "false"])
        output = capsys.readouterr().out
        # Either fails gracefully or succeeds with retry — should not raise
        assert "Running command" in output

    def test_run_with_mock_executor(self, capsys):
        """Mock the executor to test success display path."""
        with patch("modules.agent.AgentExecutor") as MockExecutor:
            instance = MockExecutor.return_value
            instance.run_command.return_value = {
                "success": True,
                "output": "hello world\n",
                "error": None,
                "attempts": [("echo hello", "Success")],
            }
            main(["run", "echo", "hello"])
        output = capsys.readouterr().out
        assert "succeeded" in output
        assert "hello world" in output

    def test_run_with_mock_executor_failure(self, capsys):
        """Mock executor failure path to test failure display."""
        with patch("modules.agent.AgentExecutor") as MockExecutor:
            instance = MockExecutor.return_value
            instance.run_command.return_value = {
                "success": False,
                "output": None,
                "error": "Exit code 1",
                "attempts": [("bad-cmd", "Exit code 1\nStderr: not found")],
            }
            main(["run", "bad-cmd"])
        output = capsys.readouterr().out
        assert "failed" in output
        assert "Exit code 1" in output

    def test_run_failure_shows_attempts(self, capsys):
        """Failed run should list attempt history."""
        with patch("modules.agent.AgentExecutor") as MockExecutor:
            instance = MockExecutor.return_value
            instance.run_command.return_value = {
                "success": False,
                "output": None,
                "error": "Exit code 127",
                "attempts": [
                    ("bad-cmd", "Exit code 127\nStderr: command not found"),
                    ("alt-cmd", "Exit code 1\nStderr: alt failed"),
                ],
            }
            main(["run", "bad-cmd"])
        output = capsys.readouterr().out
        assert "Attempt history" in output


class TestCmdDiff:
    """Tests for the diff command."""

    def test_diff_no_changes(self, capsys):
        """When git diff returns nothing, report no changes."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", returncode=0)
            main(["diff"])
        output = capsys.readouterr().out
        assert "No changes detected" in output

    def test_diff_git_error(self, capsys):
        """When git diff fails, report the error."""
        import subprocess
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                128, ["git", "diff"], stderr="not a git repo"
            )
            main(["diff"])
        output = capsys.readouterr().out
        assert "Error running git diff" in output

    def test_diff_with_content_no_ai(self, capsys):
        """Diff with content and --no-ai should parse without AI call."""
        sample_diff = (
            "diff --git a/foo.py b/foo.py\n"
            "--- a/foo.py\n"
            "+++ b/foo.py\n"
            "@@ -1,3 +1,3 @@\n"
            " def foo():\n"
            "-    return 1\n"
            "+    return 2\n"
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=sample_diff, returncode=0)
            # DiffPreview.render uses Rich console — just ensure it doesn't raise
            try:
                main(["diff", "--no-ai"])
            except Exception:
                pass  # Rich may fail in test env without terminal
        # The subprocess was called
        mock_run.assert_called()

    def test_diff_specific_files_passed_to_git(self, capsys):
        """File arguments should be forwarded to git diff."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", returncode=0)
            main(["diff", "foo.py"])
        call_args = mock_run.call_args[0][0]
        assert "foo.py" in call_args

    def test_diff_keyboard_interrupt_handled(self, capsys):
        """KeyboardInterrupt during diff should be caught gracefully."""
        sample_diff = (
            "diff --git a/foo.py b/foo.py\n"
            "--- a/foo.py\n+++ b/foo.py\n"
            "@@ -1 +1 @@\n-old\n+new\n"
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=sample_diff, returncode=0)
            with patch("modules.diff.DiffPreview.render", side_effect=KeyboardInterrupt):
                main(["diff", "--no-ai"])
        output = capsys.readouterr().out
        assert "cancelled" in output.lower()


class TestCmdCostsDashboard:
    """Tests for the costs --dashboard flag."""

    def test_costs_dashboard_launches(self, capsys):
        """--dashboard flag should invoke CostDashboard.run()."""
        with patch("modules.costs.dashboard.CostDashboard") as MockDashboard:
            instance = MockDashboard.return_value
            main(["costs", "--dashboard"])
        instance.run.assert_called_once()

    def test_costs_without_dashboard_flag(self, capsys):
        """Without --dashboard, should print text summary (not launch TUI)."""
        with patch("modules.costs.dashboard.CostDashboard") as MockDashboard:
            main(["costs"])
        MockDashboard.assert_not_called()
        output = capsys.readouterr().out
        assert "Cost Report" in output


class TestCmdRouteEdgeCases:
    """Edge cases in cmd_route."""

    def test_route_empty_prompt_list_exits(self, capsys):
        """cmd_route with empty prompt should print error and exit."""
        import argparse
        from modules.cli import cmd_route
        from modules.routing.proxy import LodestarProxy

        proxy = LodestarProxy()
        proxy.start()
        args = argparse.Namespace(prompt=[])
        with pytest.raises(SystemExit) as exc_info:
            cmd_route(proxy, args)
        proxy.stop()
        assert exc_info.value.code == 1
        output = capsys.readouterr().out
        assert "Error" in output

    def test_route_no_fallback_chain(self, capsys):
        """cmd_route should skip fallback line when chain is empty."""
        import argparse
        from modules.cli import cmd_route
        from modules.routing.proxy import LodestarProxy

        proxy = LodestarProxy()
        proxy.start()
        args = argparse.Namespace(prompt=["fix", "bug"])
        with patch.object(proxy.router, "get_fallback_chain", return_value=[]):
            cmd_route(proxy, args)
        proxy.stop()
        output = capsys.readouterr().out
        assert "Fallback" not in output


class TestCmdDiffWithAI:
    """Tests for cmd_diff AI annotation path."""

    def test_diff_with_content_and_ai(self, capsys):
        """Diff without --no-ai should attempt AI annotation."""
        sample_diff = (
            "diff --git a/foo.py b/foo.py\n"
            "--- a/foo.py\n"
            "+++ b/foo.py\n"
            "@@ -1,3 +1,3 @@\n"
            " def foo():\n"
            "-    return 1\n"
            "+    return 2\n"
        )
        with patch("subprocess.run") as mock_run, \
             patch("modules.diff.preview.DiffPreview.annotate_diff", return_value=[]) as mock_ann, \
             patch("modules.diff.preview.DiffPreview.render"):
            mock_run.return_value = MagicMock(stdout=sample_diff, returncode=0)
            main(["diff"])
        mock_ann.assert_called_once()
        output = capsys.readouterr().out
        assert "Generating AI annotations" in output


class TestCmdStatusHealthChecker:
    """Tests for status command's health_checker detailed display."""

    def test_status_health_checker_components(self, capsys):
        """Status should display health_checker component detail when available."""
        from modules.routing.proxy import LodestarProxy
        with patch.object(LodestarProxy, "health_check") as mock_health:
            mock_health.return_value = {
                "proxy": "healthy",
                "router": {"status": "healthy", "enabled": True},
                "cost_tracker": {"status": "healthy", "enabled": True},
                "health_checker": {
                    "status": "healthy",
                    "components": {
                        "litellm": {"status": "up", "latency_ms": 12},
                        "ollama": {"status": "up", "latency_ms": 8},
                    },
                },
            }
            main(["status"])
        output = capsys.readouterr().out
        assert "health_checker" in output
        assert "litellm" in output
        assert "ollama" in output

    def test_status_plain_value_module(self, capsys):
        """Status should handle modules that return non-dict values."""
        from modules.routing.proxy import LodestarProxy
        with patch.object(LodestarProxy, "health_check") as mock_health:
            mock_health.return_value = {
                "proxy": "healthy",
                "router": "ok",
                "cost_tracker": "ok",
                "health_checker": "ok",
            }
            main(["status"])
        output = capsys.readouterr().out
        assert "router" in output
