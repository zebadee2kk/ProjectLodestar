"""Cost transparency and tracking module.

Tracks per-request costs by model, calculates savings vs baseline,
provides budget alerts, and exposes CLI reporting commands.
"""

from modules.costs.tracker import CostTracker

__all__ = ["CostTracker"]
