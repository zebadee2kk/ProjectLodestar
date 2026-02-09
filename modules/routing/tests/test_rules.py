"""Tests for the tag-based routing rules engine."""

import pytest
from modules.routing.rules import RoutingRule, RulesEngine


@pytest.fixture
def engine():
    """A RulesEngine with sample rules."""
    e = RulesEngine()
    e.add_rule(RoutingRule(
        name="complex_to_claude",
        tags=["architecture", "code_review"],
        model="claude-sonnet",
        priority=10,
    ))
    e.add_rule(RoutingRule(
        name="simple_to_deepseek",
        tags=["code_generation", "bug_fix", "refactor"],
        model="gpt-3.5-turbo",
        priority=5,
    ))
    return e


class TestRoutingRule:
    """Tests for the RoutingRule dataclass."""

    def test_default_priority(self):
        rule = RoutingRule(name="test", tags=["a"], model="m")
        assert rule.priority == 0

    def test_custom_priority(self):
        rule = RoutingRule(name="test", tags=["a"], model="m", priority=99)
        assert rule.priority == 99


class TestRulesEngine:
    """Tests for the RulesEngine."""

    def test_evaluate_matches_high_priority_first(self, engine):
        # "architecture" matches both rules but claude has higher priority
        result = engine.evaluate(["architecture"])
        assert result == "claude-sonnet"

    def test_evaluate_matches_lower_priority(self, engine):
        result = engine.evaluate(["bug_fix"])
        assert result == "gpt-3.5-turbo"

    def test_evaluate_no_match_returns_default(self, engine):
        result = engine.evaluate(["unknown_tag"])
        assert result == "gpt-3.5-turbo"

    def test_evaluate_custom_default(self, engine):
        result = engine.evaluate(["unknown_tag"], default="local-llama")
        assert result == "local-llama"

    def test_evaluate_multiple_tags(self, engine):
        result = engine.evaluate(["bug_fix", "architecture"])
        # architecture rule has higher priority
        assert result == "claude-sonnet"

    def test_add_rule_sorts_by_priority(self, engine):
        engine.add_rule(RoutingRule(
            name="urgent",
            tags=["critical"],
            model="claude-opus",
            priority=100,
        ))
        assert engine.rules[0].name == "urgent"
        assert engine.rules[0].priority == 100

    def test_remove_rule(self, engine):
        assert engine.remove_rule("complex_to_claude") is True
        result = engine.evaluate(["architecture"])
        assert result == "gpt-3.5-turbo"  # default now

    def test_remove_nonexistent_rule(self, engine):
        assert engine.remove_rule("nope") is False

    def test_empty_engine_returns_default(self):
        engine = RulesEngine()
        assert engine.evaluate(["anything"]) == "gpt-3.5-turbo"

    def test_rules_property_returns_copy(self, engine):
        rules = engine.rules
        rules.clear()
        assert len(engine.rules) == 2  # original unchanged
