"""Lodestar v2 command-line interface.

Provides commands for cost reporting, route testing, and module
health checking. Uses argparse (stdlib) to avoid adding Click
as a dependency.

Usage:
    python -m modules.cli costs              # Show cost summary
    python -m modules.cli route "fix bug"    # Test routing decision
    python -m modules.cli status             # Module health check
    python -m modules.cli diff               # AI-enhanced visual diff
"""

import argparse
import sys
from typing import List, Optional

from modules.routing.proxy import LodestarProxy
from modules.costs.reporter import format_summary


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
    """Show module health status."""
    health = proxy.health_check()
    print("=== Lodestar Module Status ===")
    for module_name, status in health.items():
        if isinstance(status, dict):
            state = status.get("status", "unknown")
            enabled = status.get("enabled", "?")
            print(f"  {module_name}: {state} (enabled={enabled})")
        else:
            print(f"  {module_name}: {status}")


def cmd_diff(proxy: LodestarProxy, args: argparse.Namespace) -> None:
    """Show AI-enhanced visual diff."""
    from modules.diff import DiffPreview
    import subprocess

    # Get diff from git
    # If args.files are provided, limit to those files
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

    # Initialize DiffPreview with proxy
    # We pass an empty config for now as we don't have persistence for this module yet
    preview = DiffPreview(config={"enabled": True}, proxy=proxy)
    preview.start()

    # Parse and Render
    try:
        blocks = preview.parse_unified_diff(diff_text)
        
        # Annotate if not disabled
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
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

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

    # run
    run_parser = subparsers.add_parser(
        "run", help="Run a command with self-healing"
    )
    run_parser.add_argument(
        "command", nargs="+", help="The command to run"
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

    return parser


def main(argv: Optional[List[str]] = None) -> None:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        sys.exit(0)

    proxy = LodestarProxy()
    proxy.start()

    commands = {
        "costs": cmd_costs,
        "route": cmd_route,
        "status": cmd_status,
        "diff": cmd_diff,
        "run": cmd_run,
    }

    try:
        commands[args.command](proxy, args)
    finally:
        proxy.stop()


if __name__ == "__main__":
    main()
