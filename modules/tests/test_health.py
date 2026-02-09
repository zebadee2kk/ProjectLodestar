import pytest
from unittest.mock import Mock, patch
from modules.health.checker import HealthChecker

class TestHealthChecker:
    @pytest.fixture
    def config(self):
        return {
            "enabled": True,
            "router_url": "http://test-router",
            "ollama_url": "http://test-ollama"
        }

    @pytest.fixture
    def checker(self, config):
        return HealthChecker(config)

    def test_initialization(self, checker, config):
        assert checker.enabled is True
        assert checker.router_url == config["router_url"]
        assert checker.ollama_url == config["ollama_url"]

    @patch("requests.get")
    def test_health_check_healthy(self, mock_get, checker):
        # Mock successful responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        status = checker.health_check()

        assert status["status"] == "healthy"
        assert status["components"]["router"]["status"] == "healthy"
        assert status["components"]["ollama"]["status"] == "healthy"
        assert mock_get.call_count == 2

    @patch("requests.get")
    def test_health_check_down(self, mock_get, checker):
        # Mock connection error
        mock_get.side_effect = Exception("Connection refused")

        status = checker.health_check()

        assert status["status"] == "down"
        assert status["components"]["router"]["status"] == "down"
        assert status["components"]["ollama"]["status"] == "down"

    @patch("requests.get")
    def test_health_check_mixed(self, mock_get, checker):
        # Router works, Ollama fails
        def side_effect(url, timeout):
            if "router" in url:
                resp = Mock()
                resp.status_code = 200
                return resp
            else:
                raise Exception("Down")
        
        mock_get.side_effect = side_effect

        status = checker.health_check()

        assert status["status"] == "down"  # Overall status should be down if critical component is down
        assert status["components"]["router"]["status"] == "healthy"
        assert status["components"]["ollama"]["status"] == "down"
