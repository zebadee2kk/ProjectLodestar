"""Tests for the CostTracker."""

import pytest
from modules.costs.tracker import CostTracker, MODEL_COSTS


@pytest.fixture
def tracker_config():
    return {
        "enabled": True,
        "model_costs": MODEL_COSTS,
        "baseline_model": "claude-sonnet",
        "budget_limit": 1.0,
    }


@pytest.fixture
def tracker(tracker_config):
    t = CostTracker(tracker_config)
    t.start()
    return t


class TestCostTrackerLifecycle:

    def test_start_enabled(self, tracker_config):
        t = CostTracker(tracker_config)
        t.start()
        assert t._started is True

    def test_start_disabled(self):
        t = CostTracker({"enabled": False})
        t.start()
        assert t._started is False

    def test_stop(self, tracker):
        tracker.stop()
        assert tracker._started is False

    def test_health_check(self, tracker):
        health = tracker.health_check()
        assert health["status"] == "healthy"
        assert health["records_count"] == 0


class TestCostCalculation:

    def test_free_model_zero_cost(self, tracker):
        cost = tracker.calculate_cost("gpt-3.5-turbo", 1000, 500)
        assert cost == 0.0

    def test_claude_sonnet_cost(self, tracker):
        # 1000 input tokens * $3/M + 500 output tokens * $15/M
        cost = tracker.calculate_cost("claude-sonnet", 1000, 500)
        expected = (1000 * 3.0 + 500 * 15.0) / 1_000_000
        assert cost == round(expected, 6)

    def test_unknown_model_zero_cost(self, tracker):
        cost = tracker.calculate_cost("unknown-model", 1000, 500)
        assert cost == 0.0


class TestRecording:

    def test_record_returns_entry(self, tracker):
        entry = tracker.record("gpt-3.5-turbo", 1000, 500, task="bug_fix")
        assert entry["model"] == "gpt-3.5-turbo"
        assert entry["tokens_in"] == 1000
        assert entry["tokens_out"] == 500
        assert entry["cost"] == 0.0
        assert entry["task"] == "bug_fix"

    def test_record_calculates_savings(self, tracker):
        entry = tracker.record("gpt-3.5-turbo", 1000, 500)
        # Savings = baseline cost (claude-sonnet) - actual cost (free)
        assert entry["savings"] > 0

    def test_record_paid_model(self, tracker):
        entry = tracker.record("claude-sonnet", 1000, 500)
        assert entry["cost"] > 0
        assert entry["savings"] == 0.0  # same as baseline


class TestAggregation:

    def test_total_cost_empty(self, tracker):
        assert tracker.total_cost() == 0.0

    def test_total_cost_after_records(self, tracker):
        tracker.record("gpt-3.5-turbo", 1000, 500)
        tracker.record("claude-sonnet", 1000, 500)
        assert tracker.total_cost() > 0

    def test_total_savings(self, tracker):
        tracker.record("gpt-3.5-turbo", 10000, 5000)
        assert tracker.total_savings() > 0

    def test_savings_percentage_all_free(self, tracker):
        tracker.record("gpt-3.5-turbo", 1000, 500)
        tracker.record("gpt-3.5-turbo", 2000, 1000)
        assert tracker.savings_percentage() == 100.0

    def test_savings_percentage_all_baseline(self, tracker):
        tracker.record("claude-sonnet", 1000, 500)
        assert tracker.savings_percentage() == 0.0

    def test_savings_percentage_empty(self, tracker):
        assert tracker.savings_percentage() == 0.0


class TestBudget:

    def test_under_budget(self, tracker):
        tracker.record("gpt-3.5-turbo", 1000, 500)
        assert tracker.is_over_budget() is False

    def test_over_budget(self, tracker):
        # Record enough paid requests to exceed $1 budget
        for _ in range(200):
            tracker.record("claude-opus", 100000, 50000)
        assert tracker.is_over_budget() is True

    def test_no_budget_set(self):
        t = CostTracker({"enabled": True})
        t.record("claude-opus", 100000, 50000)
        assert t.is_over_budget() is False


class TestSummary:

    def test_summary_structure(self, tracker):
        tracker.record("gpt-3.5-turbo", 1000, 500)
        summary = tracker.summary()
        assert "total_cost" in summary
        assert "total_savings" in summary
        assert "savings_percentage" in summary
        assert "total_requests" in summary
        assert "over_budget" in summary
        assert "by_model" in summary

    def test_summary_by_model(self, tracker):
        tracker.record("gpt-3.5-turbo", 1000, 500)
        tracker.record("gpt-3.5-turbo", 2000, 1000)
        tracker.record("claude-sonnet", 500, 200)
        summary = tracker.summary()
        assert summary["by_model"]["gpt-3.5-turbo"]["requests"] == 2
        assert summary["by_model"]["claude-sonnet"]["requests"] == 1
