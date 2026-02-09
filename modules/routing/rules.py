"""Tag-based routing rules engine.

Provides a structured way to define routing rules that map
task tags to model selections with priority ordering.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class RoutingRule:
    """A single routing rule mapping tags to a model.

    Args:
        name: Human-readable rule name.
        tags: List of task tags this rule matches.
        model: Target model alias.
        priority: Higher priority rules are evaluated first.
    """

    name: str
    tags: List[str]
    model: str
    priority: int = 0


class RulesEngine:
    """Evaluates routing rules to select models by tag matching.

    Rules are evaluated in priority order (highest first). The first
    rule whose tags match the request tags wins.
    """

    def __init__(self) -> None:
        self._rules: List[RoutingRule] = []

    def add_rule(self, rule: RoutingRule) -> None:
        """Add a routing rule and re-sort by priority.

        Args:
            rule: The routing rule to add.
        """
        self._rules.append(rule)
        self._rules.sort(key=lambda r: r.priority, reverse=True)

    def remove_rule(self, name: str) -> bool:
        """Remove a rule by name.

        Args:
            name: Name of the rule to remove.

        Returns:
            True if the rule was found and removed.
        """
        before = len(self._rules)
        self._rules = [r for r in self._rules if r.name != name]
        return len(self._rules) < before

    def evaluate(
        self, tags: List[str], default: str = "gpt-3.5-turbo"
    ) -> str:
        """Find the best model for a set of tags.

        Args:
            tags: Task tags to match against rules.
            default: Fallback model if no rules match.

        Returns:
            Model alias string.
        """
        tag_set = set(tags)
        for rule in self._rules:
            if tag_set & set(rule.tags):
                return rule.model
        return default

    @property
    def rules(self) -> List[RoutingRule]:
        """Return current rules sorted by priority."""
        return list(self._rules)
