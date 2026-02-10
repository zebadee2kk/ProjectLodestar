"""Unified terminal cockpit with interactive menu for Project Lodestar."""

import time
import os
import sys
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
from rich.prompt import Prompt, IntPrompt

from modules.routing.proxy import LodestarProxy


class CockpitDashboard:
    """Renders a real-time TUI cockpit with an interactive menu.
    
    Args:
        proxy: The LodestarProxy instance to pull data from.
        refresh_rate: Update frequency in seconds for the live view.
    """

    def __init__(self, proxy: LodestarProxy, refresh_rate: float = 2.0) -> None:
        self.proxy = proxy
        self.refresh_rate = refresh_rate
        self.console = Console()
        self.running = True

    def run(self) -> None:
        """Start the interactive cockpit loop."""
        while self.running:
            # Show live dashboard for a few seconds OR just show it once and prompt
            # For a "menu" feel, we want the dashboard visible while we ask.
            layout = self._make_layout()
            self._update_layout(layout)
            
            self.console.clear()
            self.console.print(layout)
            
            # Interactive Prompt
            choice = Prompt.ask(
                "\n[bold cyan]Select Action[/bold cyan]",
                choices=["1", "2", "3", "4", "5", "q"],
                default="1"
            )
            
            if choice == "1":
                self._handle_chat()
            elif choice == "2":
                self._handle_search()
            elif choice == "3":
                self._handle_index()
            elif choice == "4":
                self._handle_costs()
            elif choice == "5":
                self._handle_health()
            elif choice == "q":
                self.running = False
                self.console.print("[yellow]Exiting Cockpit...[/yellow]")

    def _make_layout(self) -> Layout:
        """Create the dashboard layout structure."""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=4),
            Layout(name="body"),
            Layout(name="menu", size=7),
            Layout(name="footer", size=3)
        )
        
        layout["body"].split_row(
            Layout(name="left_col", ratio=1),
            Layout(name="right_col", ratio=1),
        )
        
        layout["left_col"].split_column(
            Layout(name="health", ratio=1),
            Layout(name="sessions", ratio=1),
        )
        
        layout["right_col"].split_column(
            Layout(name="costs", ratio=1),
            Layout(name="models", ratio=1),
        )
        
        return layout

    def _update_layout(self, layout: Layout) -> None:
        """Populate layout with real-time data."""
        health = self.proxy.health_check()
        cost_summary = self.proxy.cost_tracker.summary()
        
        sessions = []
        try:
             # Access via workbench module if available
             if hasattr(self.proxy, "workbench"):
                sessions = self.proxy.workbench.orchestrator.context.list_sessions()
        except:
            pass

        layout["header"].update(self._render_header())
        layout["health"].update(self._render_health(health))
        layout["costs"].update(self._render_costs(cost_summary))
        layout["sessions"].update(self._render_sessions(sessions))
        layout["models"].update(self._render_models(cost_summary))
        layout["menu"].update(self._render_menu())
        layout["footer"].update(self._render_footer())

    def _render_header(self) -> Panel:
        title = Text("🌟 PROJECT LODESTAR COCKPIT 🌟", style="bold cyan")
        v_info = Text("v2.2.0-alpha.1 | Mission Control", style="dim green")
        return Panel(Align.center(Group(title, v_info)), box=ROUNDED, border_style="cyan")

    def _render_health(self, health: Dict[str, Any]) -> Panel:
        table = Table(expand=True, box=None)
        table.add_column("Module", style="bold")
        table.add_column("Status", justify="center")
        for name, data in health.items():
            if name == "health_checker": continue
            st = data.get("status", "unknown")
            color = "green" if st == "healthy" else "red"
            table.add_row(name.replace("_", " ").title(), f"[{color}]{st.upper()}[/{color}]")
        return Panel(table, title="System Health", border_style="blue", box=ROUNDED)

    def _render_costs(self, summary: Dict[str, Any]) -> Panel:
        total = summary.get("total_cost", 0.0)
        grid = Table.grid(padding=1)
        grid.add_column(justify="right")
        grid.add_column(justify="left")
        grid.add_row("Monthly Cost:", f"[bold red]${total:.4f}[/bold red]")
        grid.add_row("Efficiency:", f"[bold yellow]{summary.get('savings_percentage',0):.1f}%[/bold yellow]")
        return Panel(Align.center(grid, vertical="middle"), title="Financials", border_style="green", box=ROUNDED)

    def _render_sessions(self, sessions: List[Dict[str, Any]]) -> Panel:
        table = Table(expand=True, box=None)
        table.add_column("Recent Sessions", style="bold magenta")
        sorted_s = sorted(sessions, key=lambda x: x.get("updated_at", ""), reverse=True)
        count = 0
        for s in sorted_s:
            if count >= 3: break
            table.add_row(f"• {s.get('name', 'Untitled')}")
            count += 1
        if not sessions: table.add_row("No active sessions")
        return Panel(table, title="Workbench", border_style="magenta", box=ROUNDED)

    def _render_models(self, summary: Dict[str, Any]) -> Panel:
        table = Table(expand=True, box=None)
        table.add_column("Top Models")
        by_model = summary.get("by_model", {})
        top = sorted(by_model.items(), key=lambda x: x[1]["requests"], reverse=True)
        count = 0
        for model, data in top:
            if count >= 3: break
            table.add_row(model.split("/")[-1])
            count += 1
        return Panel(table, title="Backends", border_style="yellow", box=ROUNDED)

    def _render_menu(self) -> Panel:
        menu_text = Text.assemble(
            ("[1] AI Chat (RAG)      ", "bold green"),
            ("[2] Search Project    ", "bold cyan"),
            ("[3] Index Repository\n", "bold yellow"),
            ("[4] Detailed Costs    ", "bold red"),
            ("[5] System Status     ", "bold blue"),
            ("[q] Exit Cockpit      ", "bold white")
        )
        return Panel(Align.center(menu_text, vertical="middle"), title="[bold white]Menu of Actions[/bold white]", box=ROUNDED, border_style="bright_black")

    def _render_footer(self) -> Panel:
        return Panel(Align.center(Text("Project Lodestar v2.2.0 | Select an action above", style="dim")), box=ROUNDED)

    # --- Action Handlers ---

    def _handle_chat(self) -> None:
        self.console.print("\n[bold green]--- AI Chat Session ---[/bold green]")
        self.console.print("[dim]Type your message or 'exit' to return to Cockpit[/dim]")
        
        while True:
            prompt = Prompt.ask("[bold green]User[/bold green]")
            if prompt.lower() in ["exit", "quit", "\\q"]:
                break
            
            with self.console.status("[bold blue]Thinking...[/bold blue]"):
                result = self.proxy.workbench.chat(prompt)
            
            self.console.print(f"\n[bold cyan]Assistant:[/bold cyan]\n{result['response']}\n")

    def _handle_search(self) -> None:
        query = Prompt.ask("\n[bold cyan]Search Query[/bold cyan]")
        if not query: return
        
        with self.console.status("[bold blue]Searching...[/bold blue]"):
            results = self.proxy.workbench.orchestrator.knowledge.search(query)
        
        table = Table(title=f"Results for '{query}'")
        table.add_column("Score", style="dim")
        table.add_column("Path", style="cyan")
        table.add_column("Snippet")
        
        for r in results[:5]:
            table.add_row(f"{r['score']:.2f}", r['metadata'].get('path', '?'), r['text'][:80].replace("\n", " ") + "...")
        
        self.console.print(table)
        Prompt.ask("\nPress Enter to return", default="")

    def _handle_index(self) -> None:
        if not Prompt.ask("[yellow]Ready to index the current repository?[/yellow]", choices=["y", "n"], default="y") == "y":
            return
            
        with self.console.status("[bold yellow]Indexing...[/bold yellow]"):
            result = self.proxy.workbench.orchestrator.knowledge.index_repository(".")
        
        self.console.print(f"[green]✅ Indexing completed: {result['indexed_files']} files indexed.[/green]")
        Prompt.ask("\nPress Enter to return", default="")

    def _handle_costs(self) -> None:
        # We can call the costs reporter logic or just show a summary
        from modules.costs.reporter import CostReporter
        reporter = CostReporter(self.proxy.cost_tracker)
        report = reporter.generate_summary()
        self.console.print(Panel(report, title="Detailed Cost Report"))
        Prompt.ask("\nPress Enter to return", default="")

    def _handle_health(self) -> None:
        # Full health check detail
        from modules.cli import cmd_status
        import argparse
        cmd_status(self.proxy, argparse.Namespace())
        Prompt.ask("\nPress Enter to return", default="")
