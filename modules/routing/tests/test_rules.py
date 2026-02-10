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

    def test_evaluate_empty_tags(self, engine):
        """Empty tags list should return default."""
        assert engine.evaluate([]) == "gpt-3.5-turbo"

    def test_evaluate_single_tag_match(self, engine):
        assert engine.evaluate(["code_generation"]) == "gpt-3.5-turbo"

    def test_add_duplicate_name_both_kept(self):
        """Adding rules with same name keeps both (no dedup)."""
        engine = RulesEngine()
        engine.add_rule(RoutingRule(name="dup", tags=["a"], model="m1", priority=1))
        engine.add_rule(RoutingRule(name="dup", tags=["b"], model="m2", priority=2))
        assert len(engine.rules) == 2

    def test_remove_duplicate_name_removes_all(self):
        """Removing by name removes all matching rules."""
        engine = RulesEngine()
        engine.add_rule(RoutingRule(name="dup", tags=["a"], model="m1"))
        engine.add_rule(RoutingRule(name="dup", tags=["b"], model="m2"))
        engine.remove_rule("dup")
        assert len(engine.rules) == 0

    def test_same_priority_preserves_insertion_stability(self):
        engine = RulesEngine()
        engine.add_rule(RoutingRule(name="first", tags=["x"], model="m1", priority=5))
        engine.add_rule(RoutingRule(name="second", tags=["y"], model="m2", priority=5))
        # Both have priority 5 — Python sort is stable so first should stay first
        assert engine.rules[0].name == "first"

    def test_tag_matching_is_set_intersection(self, engine):
        """Rule matches if ANY of its tags match ANY of the input tags."""
        # Rule "complex_to_claude" has tags ["architecture", "code_review"]
        # Only one needs to match
        assert engine.evaluate(["code_review", "unrelated"]) == "claude-sonnet"
