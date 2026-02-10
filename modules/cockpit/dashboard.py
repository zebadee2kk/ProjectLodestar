"""Unified terminal dashboard (Cockpit) for Project Lodestar."""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from rich.align import Align
from rich.box import ROUNDED
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from modules.routing.proxy import LodestarProxy


class CockpitDashboard:
    """Renders a real-time TUI cockpit for health, costs, and work sessions.
    
    Args:
        proxy: The LodestarProxy instance to pull data from.
        refresh_rate: Update frequency in seconds.
    """

    def __init__(self, proxy: LodestarProxy, refresh_rate: float = 2.0) -> None:
        self.proxy = proxy
        self.refresh_rate = refresh_rate
        self.console = Console()

    def run(self) -> None:
        """Start the live dashboard loop."""
        layout = self._make_layout()
        
        with Live(layout, refresh_per_second=1/self.refresh_rate, screen=True) as live:
            try:
                while True:
                    self._update_layout(layout)
                    time.sleep(self.refresh_rate)
            except KeyboardInterrupt:
                pass

    def _make_layout(self) -> Layout:
        """Create the initial layout structure."""
        layout = Layout()
        
        # Split into Header, Body, Footer
        layout.split_column(
            Layout(name="header", size=4),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        # Split body into Top (Health/Stats) and Bottom (Sessions/Breakdown)
        layout["body"].split_column(
            Layout(name="top_row", ratio=1),
            Layout(name="bottom_row", ratio=1),
        )
        
        layout["top_row"].split_row(
            Layout(name="health", ratio=1),
            Layout(name="costs", ratio=1),
        )
        
        layout["bottom_row"].split_row(
            Layout(name="sessions", ratio=1),
            Layout(name="models", ratio=1),
        )
        
        return layout

    def _update_layout(self, layout: Layout) -> None:
        """Update layout with fresh data."""
        health = self.proxy.health_check()
        cost_summary = self.proxy.cost_tracker.summary()
        
        # Workbench sessions (via Context module)
        # We access via proxy.workbench.orchestrator.context
        sessions = []
        try:
            sessions = self.proxy.workbench.orchestrator.context.list_sessions()
        except:
            pass

        layout["header"].update(self._render_header())
        layout["health"].update(self._render_health(health))
        layout["costs"].update(self._render_costs(cost_summary))
        layout["sessions"].update(self._render_sessions(sessions))
        layout["models"].update(self._render_models(cost_summary))
        layout["footer"].update(self._render_footer())

    def _render_header(self) -> Panel:
        """Render top header with version and time."""
        title = Text("🌟 PROJECT LODESTAR COCKPIT 🌟", style="bold cyan")
        v_info = Text("v2.2.0-alpha.1 | Persistent Project Brain", style="dim green")
        time_info = Text(f"System Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style="dim")
        
        return Panel(
            Align.center(Group(title, v_info, time_info)),
            box=ROUNDED,
            border_style="cyan"
        )

    def _render_health(self, health: Dict[str, Any]) -> Panel:
        """Render module health status."""
        table = Table(expand=True, box=None)
        table.add_column("Module", style="bold")
        table.add_column("Status", justify="center")
        table.add_column("Latency", justify="right")

        for name, data in health.items():
            if name == "health_checker": continue
            status = data.get("status", "unknown")
            color = "green" if status == "healthy" else "red" if status == "unhealthy" else "yellow"
            
            table.add_row(
                name.replace("_", " ").title(),
                f"[{color}]{status.upper()}[/{color}]",
                f"{data.get('latency_ms', 0):.0f}ms"
            )

        return Panel(table, title="[bold white]System Health[/bold white]", border_style="blue", box=ROUNDED)

    def _render_costs(self, summary: Dict[str, Any]) -> Panel:
        """Render cost overview."""
        total = summary.get("total_cost", 0.0)
        savings = summary.get("total_savings", 0.0)
        
        grid = Table.grid(padding=1)
        grid.add_column(justify="right")
        grid.add_column(justify="left")
        
        grid.add_row("Monthly Cost:", f"[bold red]${total:.4f}[/bold red]")
        grid.add_row("Total Savings:", f"[bold green]${savings:.4f}[/bold green]")
        grid.add_row("Efficiency:", f"[bold yellow]{summary.get('savings_percentage',0):.1f}%[/bold yellow]")
        grid.add_row("Total Req:", str(summary.get("total_requests", 0)))

        return Panel(Align.center(grid, vertical="middle"), title="[bold white]Financial Awareness[/bold white]", border_style="green", box=ROUNDED)

    def _render_sessions(self, sessions: List[Dict[str, Any]]) -> Panel:
        """Render recent workbench sessions."""
        table = Table(expand=True, box=None)
        table.add_column("ID", style="dim")
        table.add_column("Session Name", style="bold cyan")
        table.add_column("Updated", justify="right")

        # Show last 5 sessions
        sorted_sessions = sorted(sessions, key=lambda x: x.get("updated_at", ""), reverse=True)
        count = 0
        for s in sorted_sessions:
            if count >= 5:
                break
            count += 1
            
            ts = s.get("updated_at", "")
            if ts:
                ts = ts.split("T")[-1].split(".")[0] # Format time
            
            table.add_row(
                s.get("id", "")[:6],
                s.get("name", "Untitled"),
                ts
            )

        if not sessions:
            table.add_row("-", "No active sessions", "-")

        return Panel(table, title="[bold white]AI Workbench Activity[/bold white]", border_style="magenta", box=ROUNDED)

    def _render_models(self, summary: Dict[str, Any]) -> Panel:
        """Render top models by usage."""
        table = Table(expand=True, box=None)
        table.add_column("Model")
        table.add_column("Usage", justify="right")
        table.add_column("Cost", justify="right", style="green")

        by_model = summary.get("by_model", {})
        sorted_models = sorted(by_model.items(), key=lambda x: x[1]["requests"], reverse=True)
        count = 0
        for model, data in sorted_models:
            if count >= 5:
                break
            count += 1
            
            table.add_row(
                model.split("/")[-1], # Shorten name
                f"{data['requests']} req",
                f"${data['cost']:.3f}"
            )

        return Panel(table, title="[bold white]Top Backends[/bold white]", border_style="yellow", box=ROUNDED)

    def _render_footer(self) -> Panel:
        """Render keyboard shortcuts and tips."""
        text = Text("Press Ctrl+C to minimize Cockpit | Try 'lodestar workbench chat' for RAG support", style="dim")
        return Panel(Align.center(text), box=ROUNDED)
