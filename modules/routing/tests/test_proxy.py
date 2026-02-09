"""Tests for the LodestarProxy integration layer."""

import pytest
from modules.routing.proxy import LodestarProxy
from modules.base import EventBus


@pytest.fixture
def proxy(tmp_path):
    """A LodestarProxy with temp config directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # Write minimal modules.yaml
    (config_dir / "modules.yaml").write_text(
        "modules:\n  routing:\n    enabled: true\n  costs:\n    enabled: true\n"
    )

    # Create module config dirs
    modules_dir = tmp_path / "modules"
    routing_dir = modules_dir / "routing"
    routing_dir.mkdir(parents=True)
    (routing_dir / "config.yaml").write_text(
        "routing:\n  enabled: true\n  routing_rules:\n"
        "    code_generation: gpt-3.5-turbo\n"
        "    code_review: claude-sonnet\n"
        "    general: gpt-3.5-turbo\n"
        "  fallback_chains:\n"
        "    claude-sonnet:\n      - gpt-3.5-turbo\n"
    )

    costs_dir = modules_dir / "costs"
    costs_dir.mkdir(parents=True)
    (costs_dir / "config.yaml").write_text(
        "costs:\n  enabled: true\n  baseline_model: claude-sonnet\n"
    )

    p = LodestarProxy(config_dir=str(config_dir), event_bus=EventBus())
    p.start()
    yield p
    p.stop()


class TestProxyLifecycle:

    def test_start_and_health(self, proxy):
        health = proxy.health_check()
        assert health["proxy"] == "healthy"
        assert health["router"]["status"] == "healthy"
        assert health["cost_tracker"]["status"] == "healthy"

    def test_stop(self, proxy):
        proxy.stop()
        health = proxy.health_check()
        assert health["router"]["status"] == "down"
        assert health["cost_tracker"]["status"] == "down"


class TestProxyRouting:

    def test_dry_run_route(self, proxy):
        result = proxy.handle_request("fix the login bug")
        assert result["task"] in ("bug_fix", "code_generation", "general")
        assert result["model"] is not None

    def test_model_override(self, proxy):
        result = proxy.handle_request(
            "anything", model_override="claude-opus"
        )
        assert result["model"] == "claude-opus"

    def test_task_override(self, proxy):
        result = proxy.handle_request(
            "anything", task_override="code_review"
        )
        assert result["task"] == "code_review"

    def test_request_fn_success(self, proxy):
        result = proxy.handle_request(
            "create a new class",
            request_fn=lambda m: f"response from {m}",
        )
        assert result["result"].success is True
        assert result["result"].response is not None

    def test_request_fn_with_fallback(self, proxy):
        call_log = []

        def flaky_request(model):
            call_log.append(model)
            if model == "claude-sonnet":
                raise ConnectionError("down")
            return f"ok from {model}"

        result = proxy.handle_request(
            "review this code",
            request_fn=flaky_request,
            task_override="code_review",
        )
        # Should have fallen back from claude-sonnet to gpt-3.5-turbo
        assert result["result"].success is True
        assert "claude-sonnet" in call_log


class TestProxyEventBus:

    def test_publishes_request_completed(self, proxy):
        events = []
        proxy.event_bus.subscribe(
            "request_completed", lambda d: events.append(d)
        )
        proxy.handle_request("write a test")
        assert len(events) == 1
        assert "task" in events[0]
        assert "model" in events[0]
        assert "cost" in events[0]


class TestProxyCostTracking:

    def test_records_cost(self, proxy):
        proxy.handle_request("create a function")
        summary = proxy.cost_tracker.summary()
        assert summary["total_requests"] == 1

    def test_token_counts_forwarded(self, proxy):
        result = proxy.handle_request(
            "write a function", tokens_in=5000, tokens_out=2000
        )
        entry = result["cost_entry"]
        assert entry["tokens_in"] == 5000
        assert entry["tokens_out"] == 2000

    def test_token_counts_default_zero(self, proxy):
        result = proxy.handle_request("simple prompt")
        entry = result["cost_entry"]
        assert entry["tokens_in"] == 0
        assert entry["tokens_out"] == 0
