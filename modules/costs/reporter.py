"""CLI reporting for cost data.

Formats cost summaries for terminal output.
"""

from typing import Any, Dict


def format_summary(summary: Dict[str, Any]) -> str:
    """Format a cost summary dict as a human-readable string.

    Args:
        summary: Output from CostTracker.summary().

    Returns:
        Formatted multi-line string for terminal display.
    """
    lines = [
        "=== Lodestar Cost Report ===",
        f"Total requests:  {summary['total_requests']}",
        f"Total cost:      ${summary['total_cost']:.4f}",
        f"Total savings:   ${summary['total_savings']:.4f}",
        f"Savings:         {summary['savings_percentage']:.1f}%",
    ]

    if summary.get("over_budget"):
        lines.append("** OVER BUDGET **")

    by_model = summary.get("by_model", {})
    if by_model:
        lines.append("")
        lines.append("--- By Model ---")
        for model, data in sorted(by_model.items()):
            lines.append(
                f"  {model}: {data['requests']} reqs, "
                f"${data['cost']:.4f}, "
                f"{data['tokens']} tokens"
            )

    return "\n".join(lines)
