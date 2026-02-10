"""Lodestar Cockpit — central command hub TUI.

A full-screen Rich terminal dashboard that surfaces all Lodestar
capabilities in one place:

  • Left pane  — command menu (numbered shortcuts), orchestration playbooks
  • Right pane — live system health, cost overview, recent orchestration runs
  • Bottom bar — interactive prompt; accepts command numbers, free-text
                 orchestration requests, or a direct lodestar sub-command

Usage::

    from modules.cockpit.dashboard import LodestarCockpit
    cockpit = LodestarCockpit(proxy)
    cockpit.run()

Or from the CLI::

    lodestar cockpit
    lodestar               # no-args also launches cockpit
"""

from __future__ import annotations

import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from rich.align import Align
from rich.box import ROUNDED, SIMPLE_HEAD
from rich.columns import Columns
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.rule import Rule
from rich.style import Style
from rich.table import Table
from rich.text import Text


# ---------------------------------------------------------------------------
# Command catalogue — single source of truth for the menu
# ---------------------------------------------------------------------------

COMMANDS: List[Dict[str, str]] = [
    {"key": "1", "cmd": "costs",           "desc": "Cost summary report"},
    {"key": "2", "cmd": "costs --dashboard","desc": "Live cost dashboard (TUI)"},
    {"key": "3", "cmd": "route",           "desc": "Test routing decision"},
    {"key": "4", "cmd": "run",             "desc": "Self-healing command runner"},
    {"key": "5", "cmd": "orchestrate",     "desc": "Multi-step agent workflow"},
    {"key": "6", "cmd": "orchestrate --list", "desc": "List orchestration playbooks"},
    {"key": "7", "cmd": "orchestrate --history", "desc": "Agent run history"},
    {"key": "8", "cmd": "tournament",      "desc": "Compare models side-by-side"},
    {"key": "9", "cmd": "diff",            "desc": "AI-enhanced git diff viewer"},
    {"key": "0", "cmd": "status",          "desc": "Module health status"},
    {"key": "c", "cmd": "cache",           "desc": "Cache stats"},
    {"key": "C", "cmd": "cache --clear",   "desc": "Clear response cache"},
]

_KEY_TO_CMD: Dict[str, str] = {c["key"]: c["cmd"] for c in COMMANDS}


class LodestarCockpit:
    """Full-screen interactive terminal cockpit for ProjectLodestar.

    Combines a live-refreshing status dashboard with a command menu and
    an interactive prompt. All panel data is pulled from ``proxy``.

    Args:
        proxy: LodestarProxy instance (used for health / costs / history).
        refresh_rate: How often (seconds) to auto-refresh health/cost panels.
    """

    def __init__(self, proxy: Any, refresh_rate: float = 3.0) -> None:
        self.proxy = proxy
        self.refresh_rate = refresh_rate
        self.console = Console()
        self._last_output: List[str] = []
        self._last_command: str = ""
        self._status_msg: str = "Ready. Enter a command number or free-text request."

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Start the cockpit REPL loop."""
        while True:
            self._render_once()
            user_input = self._prompt()
            if user_input.lower() in ("q", "quit", "exit"):
                self.console.print("[dim]Goodbye.[/dim]")
                break
            if user_input:
                self._dispatch(user_input.strip())

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _render_once(self) -> None:
        """Print the full cockpit frame to the terminal."""
        self.console.clear()
        layout = self._build_layout()
        self.console.print(layout)
        if self._last_output:
            self.console.print(
                Panel(
                    "\n".join(self._last_output[-20:]),  # cap at 20 lines
                    title=f"Output — {self._last_command}",
                    border_style="dim",
                    box=ROUNDED,
                )
            )

    def _build_layout(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3),
        )
        layout["body"].split_row(
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=3),
        )
        layout["left"].split_column(
            Layout(name="commands"),
            Layout(name="playbooks", size=10),
        )
        layout["right"].split_column(
            Layout(name="health", size=10),
            Layout(name="costs_row"),
        )
        layout["costs_row"].split_row(
            Layout(name="costs"),
            Layout(name="history"),
        )

        layout["header"].update(self._render_header())
        layout["commands"].update(self._render_commands())
        layout["playbooks"].update(self._render_playbooks())
        layout["health"].update(self._render_health())
        layout["costs"].update(self._render_costs())
        layout["history"].update(self._render_history())
        layout["footer"].update(self._render_footer())
        return layout

    # ------------------------------------------------------------------
    # Panel renderers
    # ------------------------------------------------------------------

    def _render_header(self) -> Panel:
        now = datetime.now().strftime("%H:%M:%S")
        health = self._safe_health()
        overall = health.get("proxy", "unknown")
        dot = "[green]●[/green]" if overall == "healthy" else "[red]●[/red]"
        title = Text.assemble(
            ("LODESTAR COCKPIT", "bold magenta"),
            ("  v2.x", "dim"),
        )
        right = Text.assemble(
            (f"{dot} ", ""),
            (overall.upper(), "bold"),
            (f"   {now}", "dim"),
            ("   [Q]uit", "dim"),
        )
        grid = Table.grid(expand=True)
        grid.add_column()
        grid.add_column(justify="right")
        grid.add_row(title, right)
        return Panel(grid, box=ROUNDED, border_style="magenta")

    def _render_commands(self) -> Panel:
        table = Table(box=None, expand=True, show_header=False, padding=(0, 1))
        table.add_column("key", style="bold cyan", width=3)
        table.add_column("cmd", style="white")
        table.add_column("desc", style="dim")
        for c in COMMANDS:
            table.add_row(
                f"[{c['key']}]",
                c["cmd"],
                c["desc"],
            )
        return Panel(table, title="Commands", border_style="cyan", box=ROUNDED)

    def _render_playbooks(self) -> Panel:
        try:
            from modules.orchestrator import OrchestratorEngine
            import yaml
            from pathlib import Path
            cfg_path = Path("modules/orchestrator/config.yaml")
            cfg = {}
            if cfg_path.exists():
                with open(cfg_path) as fh:
                    raw = yaml.safe_load(fh) or {}
                cfg = raw.get("orchestrator", {})
            engine = OrchestratorEngine({"enabled": True, **cfg}, proxy=self.proxy)
            engine.start()
            names = engine.list_playbooks()
        except Exception:
            names = []

        table = Table(box=None, expand=True, show_header=False, padding=(0, 1))
        table.add_column("dot", width=2)
        table.add_column("name", style="yellow")
        for name in names:
            table.add_row("[yellow]▸[/yellow]", name)
        if not names:
            table.add_row("", "[dim]No playbooks found[/dim]")

        return Panel(table, title="Playbooks", border_style="yellow", box=ROUNDED)

    def _render_health(self) -> Panel:
        health = self._safe_health()
        table = Table(box=None, expand=True, show_header=False, padding=(0, 1))
        table.add_column("dot", width=3)
        table.add_column("module", style="white")
        table.add_column("detail", style="dim")

        for module, info in health.items():
            if isinstance(info, dict):
                status = info.get("status", "unknown")
                dot = "[green]●[/green]" if status == "healthy" else (
                    "[yellow]●[/yellow]" if status == "degraded" else "[red]●[/red]"
                )
                # Surface component sub-details if present
                components = info.get("components", {})
                if components:
                    table.add_row(dot, module, status)
                    for comp, cinfo in components.items():
                        cs = cinfo.get("status", "?")
                        lat = cinfo.get("latency_ms", "?")
                        cdot = "[green]●[/green]" if cs == "healthy" else "[red]●[/red]"
                        table.add_row(cdot, f"  {comp}", f"{lat}ms")
                else:
                    enabled = info.get("enabled", "?")
                    table.add_row(dot, module, f"{status} (enabled={enabled})")
            else:
                dot = "[green]●[/green]" if info == "healthy" else "[red]●[/red]"
                table.add_row(dot, module, str(info))

        return Panel(table, title="System Health", border_style="green", box=ROUNDED)

    def _render_costs(self) -> Panel:
        try:
            summary = self.proxy.cost_tracker.summary()
            total = summary.get("total_cost", 0.0)
            savings = summary.get("total_savings", 0.0)
            pct = summary.get("savings_percentage", 0.0)
            reqs = summary.get("total_requests", 0)
            over = summary.get("over_budget", False)

            cost_style = "bold red" if over else "bold green"
            grid = Table.grid(padding=(0, 1))
            grid.add_column(justify="right", style="dim")
            grid.add_column()
            grid.add_row("Total Cost", Text(f"${total:.4f}", style=cost_style))
            grid.add_row("Savings", Text(f"${savings:.4f}", style="bold cyan"))
            grid.add_row("Savings %", Text(f"{pct:.1f}%", style="bold yellow"))
            grid.add_row("Requests", Text(str(reqs), style="white"))
            if over:
                grid.add_row("", Text("OVER BUDGET", style="bold white on red"))
        except Exception as exc:
            grid = Text(f"[dim]{exc}[/dim]")

        return Panel(
            Align.center(grid, vertical="middle"),
            title="Cost Overview",
            border_style="blue",
            box=ROUNDED,
        )

    def _render_history(self) -> Panel:
        rows: List[Tuple[str, str, str, str]] = []
        try:
            from modules.orchestrator import OrchestratorEngine
            import yaml
            from pathlib import Path
            cfg_path = Path("modules/orchestrator/config.yaml")
            cfg = {}
            if cfg_path.exists():
                with open(cfg_path) as fh:
                    raw = yaml.safe_load(fh) or {}
                cfg = raw.get("orchestrator", {})
            engine = OrchestratorEngine({"enabled": True, **cfg}, proxy=self.proxy)
            engine.start()
            for r in engine.history(limit=6):
                status_style = "green" if r["status"] == "completed" else "red"
                rows.append((
                    r["run_id"],
                    f"[{status_style}]{r['status'][:4]}[/{status_style}]",
                    f"${r['cost']:.3f}",
                    (r.get("playbook") or "—")[:10],
                ))
        except Exception:
            pass

        table = Table(box=None, expand=True, show_header=True, padding=(0, 1))
        table.add_column("ID", style="dim", width=8)
        table.add_column("St", width=5)
        table.add_column("Cost", width=6)
        table.add_column("Playbook", style="yellow")
        for row in rows:
            table.add_row(*row)
        if not rows:
            table.add_row("[dim]—[/dim]", "", "", "[dim]No runs yet[/dim]")

        return Panel(table, title="Agent History", border_style="yellow", box=ROUNDED)

    def _render_footer(self) -> Panel:
        status = Text(self._status_msg, style="dim")
        hint = Text("  [Q]uit  |  [1-9,0,c,C] command  |  type request for orchestration", style="dim")
        grid = Table.grid(expand=True)
        grid.add_column()
        grid.add_column(justify="right")
        grid.add_row(status, hint)
        return Panel(grid, box=ROUNDED, border_style="dim")

    # ------------------------------------------------------------------
    # Input and dispatch
    # ------------------------------------------------------------------

    def _prompt(self) -> str:
        try:
            self.console.print("[bold cyan]>[/bold cyan] ", end="")
            return input()
        except (EOFError, KeyboardInterrupt):
            return "q"

    def _dispatch(self, user_input: str) -> None:
        """Translate user input to an action and execute it."""
        from modules.cli import build_parser, cmd_costs, cmd_route, cmd_status
        from modules.cli import cmd_run, cmd_diff, cmd_tournament, cmd_cache
        from modules.cli import cmd_orchestrate

        # Single-char shortcut → expand to command string
        if user_input in _KEY_TO_CMD:
            user_input = _KEY_TO_CMD[user_input]

        self._last_command = user_input
        self._last_output = []
        self._status_msg = f"Running: {user_input}"

        # Capture printed output
        import io
        from contextlib import redirect_stdout

        parts = user_input.split()
        if not parts:
            return

        sub = parts[0]
        argv = parts[1:]

        try:
            parser = build_parser()
            args = parser.parse_args([sub] + argv)
            dispatch = {
                "costs": cmd_costs,
                "route": cmd_route,
                "status": cmd_status,
                "run": cmd_run,
                "diff": cmd_diff,
                "tournament": cmd_tournament,
                "cache": cmd_cache,
                "orchestrate": cmd_orchestrate,
            }
            handler = dispatch.get(sub)
            if handler is None:
                # Treat as free-text orchestration request
                args = parser.parse_args(["orchestrate"] + parts)
                handler = cmd_orchestrate

            buf = io.StringIO()
            with redirect_stdout(buf):
                handler(self.proxy, args)
            output = buf.getvalue().strip()
            self._last_output = output.splitlines() if output else ["(no output)"]
            self._status_msg = f"Done: {user_input}"
        except SystemExit:
            self._last_output = [f"Invalid command: {user_input}"]
            self._status_msg = "Error — see output panel above"
        except Exception as exc:
            self._last_output = [f"Error: {exc}"]
            self._status_msg = "Error — see output panel above"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _safe_health(self) -> Dict[str, Any]:
        try:
            return self.proxy.health_check()
        except Exception:
            return {"proxy": "unknown"}
