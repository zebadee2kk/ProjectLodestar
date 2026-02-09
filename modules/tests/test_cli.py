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

    def test_no_command_shows_help(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main([])
        assert exc_info.value.code == 0
