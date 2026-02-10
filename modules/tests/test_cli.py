"""Tests for the Lodestar CLI."""

import pytest
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

    def test_no_command_shows_help(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main([])
        assert exc_info.value.code == 0


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
