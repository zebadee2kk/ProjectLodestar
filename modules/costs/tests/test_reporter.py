"""Tests for the cost reporter."""

from modules.costs.reporter import format_summary


class TestFormatSummary:

    def test_basic_output(self):
        summary = {
            "total_requests": 10,
            "total_cost": 0.05,
            "total_savings": 1.23,
            "savings_percentage": 96.1,
            "over_budget": False,
            "by_model": {
                "gpt-3.5-turbo": {"requests": 8, "cost": 0.0, "tokens": 12000},
                "claude-sonnet": {"requests": 2, "cost": 0.05, "tokens": 3000},
            },
        }
        output = format_summary(summary)
        assert "Total requests:  10" in output
        assert "$0.0500" in output
        assert "$1.2300" in output
        assert "96.1%" in output
        assert "gpt-3.5-turbo" in output
        assert "claude-sonnet" in output

    def test_over_budget_warning(self):
        summary = {
            "total_requests": 1,
            "total_cost": 100.0,
            "total_savings": 0.0,
            "savings_percentage": 0.0,
            "over_budget": True,
            "by_model": {},
        }
        output = format_summary(summary)
        assert "OVER BUDGET" in output

    def test_empty_summary(self):
        summary = {
            "total_requests": 0,
            "total_cost": 0.0,
            "total_savings": 0.0,
            "savings_percentage": 0.0,
            "over_budget": False,
            "by_model": {},
        }
        output = format_summary(summary)
        assert "Total requests:  0" in output
