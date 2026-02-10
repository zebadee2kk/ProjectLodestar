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

    def test_large_cost_values(self):
        summary = {
            "total_requests": 50000,
            "total_cost": 12345.6789,
            "total_savings": 98765.4321,
            "savings_percentage": 88.9,
            "over_budget": False,
            "by_model": {
                "claude-opus": {"requests": 50000, "cost": 12345.6789, "tokens": 500_000_000},
            },
        }
        output = format_summary(summary)
        assert "$12345.6789" in output
        assert "50000" in output

    def test_many_models(self):
        by_model = {
            f"model-{i}": {"requests": i, "cost": i * 0.01, "tokens": i * 1000}
            for i in range(8)
        }
        summary = {
            "total_requests": 28,
            "total_cost": 0.28,
            "total_savings": 0.5,
            "savings_percentage": 64.1,
            "over_budget": False,
            "by_model": by_model,
        }
        output = format_summary(summary)
        # All 8 models should appear
        for i in range(8):
            assert f"model-{i}" in output

    def test_models_sorted_alphabetically(self):
        summary = {
            "total_requests": 3,
            "total_cost": 0.01,
            "total_savings": 0.02,
            "savings_percentage": 66.7,
            "over_budget": False,
            "by_model": {
                "zebra-model": {"requests": 1, "cost": 0.005, "tokens": 100},
                "alpha-model": {"requests": 1, "cost": 0.003, "tokens": 100},
                "middle-model": {"requests": 1, "cost": 0.002, "tokens": 100},
            },
        }
        output = format_summary(summary)
        alpha_pos = output.index("alpha-model")
        middle_pos = output.index("middle-model")
        zebra_pos = output.index("zebra-model")
        assert alpha_pos < middle_pos < zebra_pos

    def test_report_header(self):
        summary = {
            "total_requests": 1, "total_cost": 0.0, "total_savings": 0.0,
            "savings_percentage": 0.0, "over_budget": False, "by_model": {},
        }
        output = format_summary(summary)
        assert "Lodestar Cost Report" in output

    def test_no_over_budget_when_false(self):
        summary = {
            "total_requests": 1, "total_cost": 0.01, "total_savings": 0.0,
            "savings_percentage": 0.0, "over_budget": False, "by_model": {},
        }
        output = format_summary(summary)
        assert "OVER BUDGET" not in output
