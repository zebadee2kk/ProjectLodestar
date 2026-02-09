"""Terminal dashboard for real-time cost tracking."""

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

from modules.costs.tracker import CostTracker


class CostDashboard:
    """Renders a real-time TUI dashboard for cost metrics.
    
    Args:
        tracker: The CostTracker instance to pull data from.
        refresh_rate: Update frequency in seconds.
    """

    def __init__(self, tracker: CostTracker, refresh_rate: float = 1.0) -> None:
        self.tracker = tracker
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
        
        # Split into Header (top), Body (middle), Footer (bottom)
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        # Split body into main stats and detailed table
        layout["body"].split_row(
            Layout(name="stats", ratio=1),
            Layout(name="details", ratio=2),
        )
        
        return layout

    def _update_layout(self, layout: Layout) -> None:
        """Update layout with fresh data."""
        summary = self.tracker.summary()
        
        # Header
        layout["header"].update(self._render_header())
        
        # Stats (Left Panel)
        layout["stats"].update(self._render_stats(summary))
        
        # Details (Right Panel)
        layout["details"].update(self._render_details(summary))
        
        # Footer
        layout["footer"].update(self._render_footer(summary))

    def _render_header(self) -> Panel:
        """Render the top header."""
        title = Text("Lodestar Cost Transparency Dashboard", style="bold magenta")
        subtitle = Text(f"Last updated: {datetime.now().strftime('%H:%M:%S')}", style="dim")
        return Panel(Align.center(Group(title, subtitle)), box=ROUNDED)

    def _render_stats(self, summary: Dict[str, Any]) -> Panel:
        """Render high-level statistics."""
        total_cost = summary["total_cost"]
        savings = summary["total_savings"]
        pct = summary["savings_percentage"]
        
        cost_text = Text(f"${total_cost:.4f}", style="bold red" if summary.get("over_budget") else "bold green")
        savings_text = Text(f"${savings:.4f}", style="bold cyan")
        pct_text = Text(f"{pct:.1f}%", style="bold yellow")
        
        grid = Table.grid(padding=1)
        grid.add_column(justify="right")
        grid.add_column(justify="left")
        
        grid.add_row("Total Cost:", cost_text)
        grid.add_row("Total Savings:", savings_text)
        grid.add_row("Savings %:", pct_text)
        grid.add_row("Total Requests:", str(summary["total_requests"]))
        
        return Panel(
            Align.center(grid, vertical="middle"),
            title="Overview",
            border_style="blue",
            box=ROUNDED
        )

    def _render_details(self, summary: Dict[str, Any]) -> Panel:
        """Render detailed breakdown table."""
        table = Table(expand=True, box=None)
        table.add_column("Model", style="cyan")
        table.add_column("Requests", justify="right")
        table.add_column("Tokens", justify="right")
        table.add_column("Cost", justify="right", style="green")
        
        by_model = summary.get("by_model", {})
        for model, data in sorted(by_model.items(), key=lambda x: x[1]["cost"], reverse=True):
            table.add_row(
                model,
                str(data["requests"]),
                f"{data['tokens']:,}",
                f"${data['cost']:.4f}"
            )
            
        return Panel(
            table,
            title="Breakdown by Model",
            border_style="green",
            box=ROUNDED
        )

    def _render_footer(self, summary: Dict[str, Any]) -> Panel:
        """Render status footer."""
        if summary.get("over_budget"):
            status = Text("⚠️  OVER BUDGET LIMIT", style="bold white on red")
        else:
            status = Text("✅  Within Budget", style="bold white on green")
            
        return Panel(Align.center(status), box=ROUNDED)
