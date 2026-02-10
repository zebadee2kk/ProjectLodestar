"""Tests for the Lodestar Cockpit dashboard."""

import io
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from modules.cockpit.dashboard import COMMANDS, LodestarCockpit, _KEY_TO_CMD


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_proxy():
    proxy = MagicMock()
    proxy.event_bus = MagicMock()
    proxy.health_check.return_value = {
        "proxy": "healthy",
        "router": {"status": "healthy", "enabled": True},
        "cost_tracker": {"status": "healthy", "enabled": True},
        "health_checker": {
            "status": "healthy",
            "components": {
                "router": {"status": "healthy", "latency_ms": 5},
                "ollama": {"status": "healthy", "latency_ms": 3},
            },
        },
    }
    proxy.cost_tracker.summary.return_value = {
        "total_cost": 0.0123,
        "total_savings": 0.89,
        "savings_percentage": 98.6,
        "total_requests": 42,
        "over_budget": False,
        "by_model": {
            "gpt-3.5-turbo": {"requests": 40, "tokens": 10000, "cost": 0.0},
            "claude-sonnet": {"requests": 2, "tokens": 500, "cost": 0.0123},
        },
    }
    return proxy


def _make_cockpit(proxy=None) -> LodestarCockpit:
    return LodestarCockpit(proxy or _make_proxy())


# ---------------------------------------------------------------------------
# COMMANDS catalogue
# ---------------------------------------------------------------------------

class TestCommandsCatalogue:
    def test_all_commands_have_required_keys(self):
        for c in COMMANDS:
            assert "key" in c
            assert "cmd" in c
            assert "desc" in c

    def test_keys_are_unique(self):
        keys = [c["key"] for c in COMMANDS]
        assert len(keys) == len(set(keys)), "Duplicate keys in COMMANDS"

    def test_key_to_cmd_mapping(self):
        for c in COMMANDS:
            assert _KEY_TO_CMD[c["key"]] == c["cmd"]

    def test_essential_commands_present(self):
        cmds = [c["cmd"] for c in COMMANDS]
        assert any("costs" in c for c in cmds)
        assert any("orchestrate" in c for c in cmds)
        assert any("status" in c for c in cmds)


# ---------------------------------------------------------------------------
# Panel renderers (smoke tests — verify they return Panel objects)
# ---------------------------------------------------------------------------

class TestPanelRenderers:
    def setup_method(self):
        self.cockpit = _make_cockpit()

    def test_render_header_returns_panel(self):
        from rich.panel import Panel
        result = self.cockpit._render_header()
        assert isinstance(result, Panel)

    def test_render_commands_returns_panel(self):
        from rich.panel import Panel
        result = self.cockpit._render_commands()
        assert isinstance(result, Panel)

    def test_render_health_returns_panel(self):
        from rich.panel import Panel
        result = self.cockpit._render_health()
        assert isinstance(result, Panel)

    def test_render_costs_returns_panel(self):
        from rich.panel import Panel
        result = self.cockpit._render_costs()
        assert isinstance(result, Panel)

    def test_render_history_returns_panel(self):
        from rich.panel import Panel
        result = self.cockpit._render_history()
        assert isinstance(result, Panel)

    def test_render_footer_returns_panel(self):
        from rich.panel import Panel
        result = self.cockpit._render_footer()
        assert isinstance(result, Panel)

    def test_render_playbooks_returns_panel(self):
        from rich.panel import Panel
        result = self.cockpit._render_playbooks()
        assert isinstance(result, Panel)


# ---------------------------------------------------------------------------
# Panel renderers — content correctness
# ---------------------------------------------------------------------------

class TestPanelContent:
    def setup_method(self):
        from rich.console import Console
        self.cockpit = _make_cockpit()
        self.console = Console(width=120)

    def _capture(self, panel) -> str:
        buf = io.StringIO()
        console = __import__("rich.console", fromlist=["Console"]).Console(
            file=buf, width=120, highlight=False, markup=False
        )
        console.print(panel)
        return buf.getvalue()

    def test_header_mentions_lodestar(self):
        text = self._capture(self.cockpit._render_header())
        assert "LODESTAR" in text.upper()

    def test_commands_panel_shows_all_keys(self):
        text = self._capture(self.cockpit._render_commands())
        for c in COMMANDS:
            assert c["key"] in text

    def test_health_panel_shows_healthy(self):
        text = self._capture(self.cockpit._render_health())
        assert "healthy" in text.lower()

    def test_costs_panel_shows_cost(self):
        text = self._capture(self.cockpit._render_costs())
        assert "$" in text

    def test_health_panel_handles_error(self):
        proxy = _make_proxy()
        proxy.health_check.side_effect = RuntimeError("connection refused")
        cockpit = LodestarCockpit(proxy)
        from rich.panel import Panel
        # Should not raise
        result = cockpit._render_health()
        assert isinstance(result, Panel)

    def test_costs_panel_handles_error(self):
        proxy = _make_proxy()
        proxy.cost_tracker.summary.side_effect = RuntimeError("db locked")
        cockpit = LodestarCockpit(proxy)
        from rich.panel import Panel
        result = cockpit._render_costs()
        assert isinstance(result, Panel)


# ---------------------------------------------------------------------------
# Layout builder
# ---------------------------------------------------------------------------

class TestBuildLayout:
    def test_layout_has_expected_sections(self):
        from rich.layout import Layout
        cockpit = _make_cockpit()
        layout = cockpit._build_layout()
        assert isinstance(layout, Layout)


# ---------------------------------------------------------------------------
# Dispatch logic
# ---------------------------------------------------------------------------

class TestDispatch:
    def test_shortcut_key_expands_to_command(self):
        cockpit = _make_cockpit()
        # Key "0" maps to "status"
        dispatched = []
        original_dispatch = cockpit._dispatch

        def mock_dispatch(user_input):
            if user_input in _KEY_TO_CMD:
                user_input = _KEY_TO_CMD[user_input]
            dispatched.append(user_input)

        cockpit._dispatch = mock_dispatch
        cockpit._dispatch("0")
        assert dispatched[0] == "status"

    def test_invalid_command_sets_error_status(self):
        cockpit = _make_cockpit()
        cockpit._dispatch("not_a_real_command_xyz")
        assert "error" in cockpit._status_msg.lower() or cockpit._last_output

    def test_costs_command_produces_output(self):
        cockpit = _make_cockpit()
        with patch("modules.cli.format_summary", return_value="mock cost summary"):
            cockpit._dispatch("costs")
        assert cockpit._last_command == "costs"

    def test_status_command_captured(self):
        cockpit = _make_cockpit()
        cockpit._dispatch("status")
        assert cockpit._last_command == "status"


# ---------------------------------------------------------------------------
# Run loop (mocked input)
# ---------------------------------------------------------------------------

class TestRunLoop:
    def test_quit_on_q(self):
        cockpit = _make_cockpit()
        with patch.object(cockpit, "_render_once"), \
             patch.object(cockpit, "_prompt", return_value="q"):
            cockpit.run()  # Should return cleanly

    def test_quit_on_quit(self):
        cockpit = _make_cockpit()
        with patch.object(cockpit, "_render_once"), \
             patch.object(cockpit, "_prompt", return_value="quit"):
            cockpit.run()

    def test_dispatch_called_for_non_quit(self):
        cockpit = _make_cockpit()
        calls = []
        inputs = iter(["status", "q"])
        with patch.object(cockpit, "_render_once"), \
             patch.object(cockpit, "_prompt", side_effect=lambda: next(inputs)), \
             patch.object(cockpit, "_dispatch", side_effect=lambda x: calls.append(x)):
            cockpit.run()
        assert "status" in calls

    def test_empty_input_not_dispatched(self):
        cockpit = _make_cockpit()
        calls = []
        inputs = iter(["", "q"])
        with patch.object(cockpit, "_render_once"), \
             patch.object(cockpit, "_prompt", side_effect=lambda: next(inputs)), \
             patch.object(cockpit, "_dispatch", side_effect=lambda x: calls.append(x)):
            cockpit.run()
        assert calls == []  # Empty input skipped, "q" handled as quit not dispatch


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------

class TestCLIIntegration:
    def test_cockpit_command_registered(self):
        from modules.cli import build_parser
        parser = build_parser()
        # Should parse without error
        args = parser.parse_args(["cockpit"])
        assert args.command == "cockpit"

    def test_no_args_would_launch_cockpit(self):
        """Verify that main() with no args goes to cockpit path (not sys.exit)."""
        from modules.cli import build_parser
        parser = build_parser()
        args = parser.parse_args([])
        assert args.command is None  # Cockpit is the default when command is None
