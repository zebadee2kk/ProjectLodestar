"""AI annotation engine for diff blocks.

Generates explanations and confidence scores for code changes.
This is a placeholder that will integrate with LLM providers
when the routing module is fully operational.
"""

from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class DiffAnnotator:
    """Generates AI annotations for diff blocks.

    Currently uses heuristic-based annotation. Will be extended
    to call LLM providers via the routing module for richer
    explanations.
    """

    # Simple heuristic patterns for annotation
    PATTERNS: Dict[str, Tuple[str, float]] = {
        "def ": ("Function definition changed", 0.9),
        "class ": ("Class definition changed", 0.9),
        "import ": ("Import statement modified", 0.95),
        "return ": ("Return value changed", 0.8),
        "raise ": ("Exception handling modified", 0.85),
        "if ": ("Conditional logic changed", 0.7),
        "for ": ("Loop logic changed", 0.7),
        "try:": ("Error handling modified", 0.8),
    }

    def annotate_lines(self, lines: list[str]) -> Tuple[str, float]:
        """Generate a heuristic annotation for a set of diff lines.

        Args:
            lines: List of diff lines (prefixed with +, -, or space).

        Returns:
            Tuple of (annotation_text, confidence_score).
        """
        added = [l[1:] for l in lines if l.startswith("+")]
        removed = [l[1:] for l in lines if l.startswith("-")]

        if not added and not removed:
            return "No changes detected", 1.0

        # Check added lines for known patterns
        for line in added:
            stripped = line.strip()
            for pattern, (desc, conf) in self.PATTERNS.items():
                if stripped.startswith(pattern):
                    return desc, conf

        # Check removed lines for known patterns
        for line in removed:
            stripped = line.strip()
            for pattern, (desc, conf) in self.PATTERNS.items():
                if stripped.startswith(pattern):
                    return f"{desc} (removed)", conf

        # Fallback
        if added and not removed:
            return f"Added {len(added)} line(s)", 0.6
        elif removed and not added:
            return f"Removed {len(removed)} line(s)", 0.6
        else:
            return f"Modified {len(added)} line(s)", 0.5
