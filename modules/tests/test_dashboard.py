import pytest
from unittest.mock import MagicMock
from modules.costs.dashboard import CostDashboard
from modules.costs.tracker import CostTracker
from rich.layout import Layout
from rich.panel import Panel

class TestCostDashboard:
    @pytest.fixture
    def mock_tracker(self):
        tracker = MagicMock(spec=CostTracker)
        tracker.summary.return_value = {
            "total_cost": 10.50,
            "total_savings": 5.00,
            "savings_percentage": 30.0,
            "total_requests": 100,
            "over_budget": False,
            "by_model": {
                "gpt-4o": {"requests": 50, "cost": 8.00, "tokens": 1000},
                "gpt-4o-mini": {"requests": 50, "cost": 2.50, "tokens": 5000},
            }
        }
        return tracker

    def test_init(self, mock_tracker):
        dashboard = CostDashboard(mock_tracker)
        assert dashboard.tracker == mock_tracker
        assert dashboard.console is not None

    def test_make_layout(self, mock_tracker):
        dashboard = CostDashboard(mock_tracker)
        layout = dashboard._make_layout()
        assert isinstance(layout, Layout)
        assert layout["header"] is not None
        assert layout["body"] is not None
        assert layout["footer"] is not None

    def test_render_components(self, mock_tracker):
        dashboard = CostDashboard(mock_tracker)
        summary = mock_tracker.summary()
        
        # Test Header
        header = dashboard._render_header()
        assert isinstance(header, Panel)
        
        # Test Stats
        stats = dashboard._render_stats(summary)
        assert isinstance(stats, Panel)
        
        # Test Details
        details = dashboard._render_details(summary)
        assert isinstance(details, Panel)
        
        # Test Footer
        footer = dashboard._render_footer(summary)
        assert isinstance(footer, Panel)
