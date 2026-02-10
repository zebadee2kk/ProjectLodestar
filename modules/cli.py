"""Lodestar v2 command-line interface.

Provides commands for cost reporting, route testing, tournament
matches, and module health checking. Uses argparse (stdlib) to
avoid adding Click as a dependency.

Usage:
    python -m modules.cli costs              # Show cost summary
    python -m modules.cli route "fix bug"    # Test routing decision
    python -m modules.cli tournament "prompt" model1 model2  # Run tournament
    python -m modules.cli status             # Module health check
    python -m modules.cli diff               # AI-enhanced visual diff
"""

import argparse
import sys
from typing import List, Optional

from modules.routing.proxy import LodestarProxy
from modules.costs.reporter import format_summary
from modules.tournament.runner import TournamentRunner


def cmd_costs(proxy: LodestarProxy, args: argparse.Namespace) -> None:
    """Show cost summary or launch dashboard."""
    if args.dashboard:
        from modules.costs.dashboard import CostDashboard
        dashboard = CostDashboard(proxy.cost_tracker)
        dashboard.run()
    else:
        summary = proxy.cost_tracker.summary()
        print(format_summary(summary))


def cmd_config(proxy: LodestarProxy, args: argparse.Namespace) -> None:
    """Configure local settings (credentials, hosts)."""
    import yaml
    from pathlib import Path
    from rich.console import Console

    console = Console()
    config_dir = Path(".lodestar")
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "config.yaml"

    current_config = {}
    if config_file.exists():
        try:
            with open(config_file) as f:
                current_config = yaml.safe_load(f) or {}
        except Exception:
            current_config = {}

    console.print("\n[bold cyan]🔧 Lodestar Local Configuration[/bold cyan]")
    console.print("Settings stored in .lodestar/config.yaml (git-ignored)\n")

    if "health" not in current_config:
        current_config["health"] = {}
    h_cfg = current_config["health"]
    
    # GPU Settings
    console.print("[bold]Remote GPU (SSH)[/bold]")
    gpu_host = input(f"  Host/IP [{h_cfg.get('gpu_ssh_host', 'None')}]: ").strip()
    gpu_user = input(f"  SSH User [{h_cfg.get('gpu_ssh_user', 'None')}]: ").strip()

    if gpu_host:
        h_cfg["gpu_ssh_host"] = gpu_host
    if gpu_user:
        h_cfg["gpu_ssh_user"] = gpu_user

    with open(config_file, "w") as f:
        yaml.dump(current_config, f, default_flow_style=False)

    console.print(f"\n[green]✅ Configuration saved successfully![/green]")
    console.print("[dim]Run './lodestar status' to verify connectivity.[/dim]\n")


def cmd_run(proxy: LodestarProxy, args: argparse.Namespace) -> None:
    """Run a command with self-healing capabilities."""
    from modules.agent import AgentExecutor
    import shlex

    # Join the command parts if it's a list
    command = " ".join(args.command)
    print(f"Running command: {command}")
    
    executor = AgentExecutor(proxy)
    result = executor.run_command(command)
    
    if result["success"]:
        print("Command succeeded!")
        print(result["output"])
    else:
        print("Command failed after retries.")
        print(f"Last error: {result['error']}")
        print("Attempt history:")
        for i, (cmd, out) in enumerate(result["attempts"]):
            print(f"  {i+1}. `{cmd}` -> {out[:100]}...")


def cmd_cache(proxy: LodestarProxy, args: argparse.Namespace) -> None:
    """Manage response cache."""
    if args.clear:
        count = proxy.cache.clear()
        print(f"Cache cleared. Removed {count} entries.")
    else:
        stats = proxy.cache.stats()
        print("=== Cache Stats ===")
        print(f"Entries: {stats['entries']}")
        print(f"Size:    {stats['size_bytes']} bytes")
        print(f"Path:    {stats['db_path']}")


def cmd_route(proxy: LodestarProxy, args: argparse.Namespace) -> None:
    """Test routing decision for a prompt."""
    prompt = " ".join(args.prompt)
    if not prompt:
        print("Error: provide a prompt to test routing")
        sys.exit(1)

    result = proxy.handle_request(prompt)
    task = result["task"]
    model = result["model"]
    chain = proxy.router.get_fallback_chain(model)

    print(f"Prompt:   {prompt}")
    print(f"Task:     {task}")
    print(f"Model:    {model}")
    if chain:
        print(f"Fallback: {' -> '.join(chain)}")


def cmd_status(proxy: LodestarProxy, args: argparse.Namespace) -> None:
    """Show module health status with hardware metrics."""
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.columns import Columns

    health = proxy.health_check()
    console = Console()

    # Title
    console.print(Panel("[bold cyan]🌟 Lodestar System Status[/bold cyan]", border_style="cyan"))

    # Core Modules Table
    module_table = Table(title="Core Modules", box=None, show_header=False)
    for name, data in health.items():
        if name == "health_checker": continue
        
        status = data.get("status", "unknown") if isinstance(data, dict) else str(data)
        color = "green" if status == "healthy" else "red"
        module_table.add_row(f"[bold]{name}[/bold]", f"[{color}]{status}[/]")
    
    # Components / Endpoints
    comp_table = Table(title="Endpoints", box=None, show_header=False)
    checker = health.get("health_checker", {})
    components = checker.get("components", {})
    
    for comp, details in components.items():
        if comp == "gpu": continue # Handle GPU separately for richer display
        
        st = details.get("status", "unknown")
        color = "green" if st == "healthy" else "red"
        lat = details.get('latency_ms', '?')
        comp_table.add_row(f"  • {comp}", f"[{color}]{st}[/]", f"({lat}ms)")

    # GPU Hardware Section
    gpu = components.get("gpu", {})
    gpu_panel = None
    if gpu.get("status") == "healthy":
        gpu_panel = Panel(
            f"[bold green]✓[/bold green] {gpu.get('name')}\n"
            f"[dim]Temp:[/dim] [bold]{gpu.get('temp_c')}°C[/bold] | "
            f"[dim]Load:[/dim] [bold]{gpu.get('load_pct')}%[/bold]\n"
            f"[dim]VRAM:[/dim] [bold]{gpu.get('memory_used_mb')}/{gpu.get('memory_total_mb')} MiB[/bold] ({gpu.get('memory_pct')}%)",
            title="GPU Hardware (T600)",
            border_style="green",
            expand=False
        )
    elif gpu.get("status") == "not_available":
         gpu_panel = Panel("[dim]GPU Hardware: Not Detected[/dim]\n[dim]Run 'lodestar config' to set up remote GPU.[/dim]", border_style="dim", expand=False)
    else:
         gpu_panel = Panel(
             f"[bold red]![/bold red] GPU Error: {gpu.get('error', 'Unknown')}\n"
             f"[dim]Tip: Check SSH access or run 'lodestar config'[/dim]", 
             border_style="red", 
             expand=False
         )

    # Layout Rendering
    console.print(Columns([module_table, comp_table]))
    if gpu_panel:
        console.print(gpu_panel)
    console.print("")


def cmd_tournament(proxy: LodestarProxy, args: argparse.Namespace) -> None:
    """Run a tournament match between models (dry-run without API credits)."""
    prompt = args.prompt
    models = args.models

    runner = TournamentRunner({"enabled": True, "default_models": models})
    runner.start()

    def dry_run_fn(model, prompt_text):
        return f"[dry-run] {model} would respond to: {prompt_text[:50]}"

    result = runner.run_match(prompt, dry_run_fn, models=models)
    print(runner.format_match(result))
    runner.stop()


def cmd_diff(proxy: LodestarProxy, args: argparse.Namespace) -> None:
    """Show AI-enhanced visual diff."""
    from modules.diff import DiffPreview
    import subprocess

    # Get diff from git
    cmd = ["git", "diff"] + args.files
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        diff_text = result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running git diff: {e}")
        return

    if not diff_text:
        print("No changes detected.")
        return

    preview = DiffPreview(config={"enabled": True}, proxy=proxy)
    preview.start()

    try:
        blocks = preview.parse_unified_diff(diff_text)

        if not args.no_ai:
            print("Generating AI annotations... (Ctrl+C to skip)")
            blocks = preview.annotate_diff(blocks)

        preview.render(blocks)
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
    finally:
        preview.stop()


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="lodestar",
        description="ProjectLodestar v2 - AI development environment CLI",
    )
    subparsers = parser.add_subparsers(dest="action", help="Available commands")

    # costs
    cost_parser = subparsers.add_parser("costs", help="Show cost summary report")
    cost_parser.add_argument(
        "--dashboard", "-d", action="store_true", help="Launch interactive TUI dashboard"
    )

    # route
    route_parser = subparsers.add_parser(
        "route", help="Test routing decision for a prompt"
    )
    route_parser.add_argument(
        "prompt", nargs="+", help="The prompt to test routing for"
    )

    # tournament
    tournament_parser = subparsers.add_parser(
        "tournament", help="Run a tournament match between models"
    )
    tournament_parser.add_argument(
        "prompt", help="The prompt to send to all models"
    )
    tournament_parser.add_argument(
        "models", nargs="+", help="Models to compare (at least 2)"
    )

    # run
    run_parser = subparsers.add_parser(
        "run", help="Run a command with self-healing"
    )
    run_parser.add_argument(
        "command", nargs=argparse.REMAINDER, help="The command to run"
    )

    # cache
    cache_parser = subparsers.add_parser("cache", help="Manage response cache")
    cache_parser.add_argument(
        "--clear", action="store_true", help="Clear all cache entries"
    )

    # status
    subparsers.add_parser("status", help="Show module health status")

    # diff
    diff_parser = subparsers.add_parser(
        "diff", help="Show AI-enhanced visual diff"
    )
    diff_parser.add_argument(
        "files", nargs="*", help="Specific files to diff"
    )
    diff_parser.add_argument(
        "--no-ai", action="store_true", help="Disable AI annotations"
    )

    # config
    subparsers.add_parser("config", help="Configure local settings and credentials")

    return parser


def main(argv: Optional[List[str]] = None) -> None:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.action:
        parser.print_help()
        sys.exit(0)

    proxy = LodestarProxy()
    proxy.start()

    commands = {
        "costs": cmd_costs,
        "route": cmd_route,
        "tournament": cmd_tournament,
        "status": cmd_status,
        "diff": cmd_diff,
        "run": cmd_run,
        "cache": cmd_cache,
        "config": cmd_config,
    }

    try:
        commands[args.action](proxy, args)
    finally:
        proxy.stop()


if __name__ == "__main__":
    main()
