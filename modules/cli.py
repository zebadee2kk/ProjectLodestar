"""Lodestar v2 command-line interface.

Provides commands for cost reporting, route testing, and module
health checking. Uses argparse (stdlib) to avoid adding Click
as a dependency.

Usage:
    python -m modules.cli costs              # Show cost summary
    python -m modules.cli route "fix bug"    # Test routing decision
    python -m modules.cli status             # Module health check
"""

import argparse
import sys
from typing import List, Optional

from modules.routing.proxy import LodestarProxy
from modules.costs.reporter import format_summary


def cmd_costs(proxy: LodestarProxy, args: argparse.Namespace) -> None:
    """Show cost summary report."""
    summary = proxy.cost_tracker.summary()
    print(format_summary(summary))


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


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="lodestar",
        description="ProjectLodestar v2 - AI development environment CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # costs
    subparsers.add_parser("costs", help="Show cost summary report")

    # route
    route_parser = subparsers.add_parser(
        "route", help="Test routing decision for a prompt"
    )
    route_parser.add_argument(
        "prompt", nargs="+", help="The prompt to test routing for"
    )

    # status
    subparsers.add_parser("status", help="Show module health status")

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
    }

    try:
        commands[args.command](proxy, args)
    finally:
        proxy.stop()


if __name__ == "__main__":
    main()
