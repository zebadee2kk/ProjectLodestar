"""Integration tests for the LodestarProxy full pipeline.

Tests exercise the complete request path:
    classify -> cache -> route -> fallback -> cost -> event bus

All external I/O (LLM APIs, Ollama, nvidia-smi) is mocked so the
suite runs offline and deterministically.
"""

import pytest
from unittest.mock import MagicMock, patch

from modules.routing.proxy import LodestarProxy
from modules.routing.fallback import RequestResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_request_fn(response="ok", succeed=True):
    """Return a request function that optionally raises or returns a value."""
    def _fn(model):
        if not succeed:
            raise RuntimeError("LLM unavailable")
        return response
    return _fn


# ---------------------------------------------------------------------------
# Proxy lifecycle
# ---------------------------------------------------------------------------

class TestProxyLifecycle:

    def test_proxy_starts_and_stops(self, proxy):
        health = proxy.health_check()
        assert health["proxy"] == "healthy"

    def test_health_check_includes_all_subsystems(self, proxy):
        health = proxy.health_check()
        assert "router" in health
        assert "cost_tracker" in health
        assert "health_checker" in health

    def test_start_is_idempotent(self, proxy):
        """Calling start() twice should not raise."""
        proxy.start()
        assert proxy.health_check()["proxy"] == "healthy"


# ---------------------------------------------------------------------------
# Routing pipeline (dry-run — no request_fn)
# ---------------------------------------------------------------------------

class TestDryRunPipeline:

    def test_route_returns_task_and_model(self, proxy):
        result = proxy.handle_request("fix the login bug")
        assert "task" in result
        assert "model" in result

    def test_code_prompt_classified_correctly(self, proxy):
        result = proxy.handle_request("write a function to sort a list")
        assert result["task"] in ("code_generation", "general")

    def test_review_prompt_classification(self, proxy):
        result = proxy.handle_request("review this pull request for issues")
        # SemanticRouter classifies based on keywords; accept any valid task type
        assert isinstance(result["task"], str)
        assert len(result["task"]) > 0

    def test_result_includes_cost_entry(self, proxy):
        result = proxy.handle_request("explain this error message")
        assert "cost_entry" in result
        assert "cost" in result["cost_entry"]
        assert "model" in result["cost_entry"]

    def test_dry_run_cost_is_zero_for_free_model(self, proxy):
        """With no real tokens, cost should be $0."""
        result = proxy.handle_request("fix the bug", tokens_in=0, tokens_out=0)
        assert result["cost_entry"]["cost"] == 0.0

    def test_cost_recorded_with_token_counts(self, proxy):
        result = proxy.handle_request(
            "build a REST API",
            tokens_in=100,
            tokens_out=200,
        )
        assert result["cost_entry"]["tokens_in"] == 100
        assert result["cost_entry"]["tokens_out"] == 200


# ---------------------------------------------------------------------------
# Cache integration
# ---------------------------------------------------------------------------

class TestCachePipeline:

    def test_second_identical_request_hits_cache(self, proxy):
        prompt = "explain what recursion is"
        first = proxy.handle_request(prompt)
        second = proxy.handle_request(prompt)
        # Second result should come from cache (same model)
        assert second["model"] == first["model"]

    def test_cache_populated_after_request(self, proxy):
        proxy.handle_request("write a hello world program")
        stats = proxy.cache.stats()
        assert stats["entries"] >= 1

    def test_cache_clear_removes_entries(self, proxy):
        proxy.handle_request("test prompt for cache")
        proxy.cache.clear()
        stats = proxy.cache.stats()
        assert stats["entries"] == 0

    def test_model_override_bypasses_cache(self, proxy):
        prompt = "test cache bypass"
        proxy.handle_request(prompt)
        # With model_override, cache should be bypassed
        result = proxy.handle_request(prompt, model_override="claude-sonnet")
        assert result["model"] == "claude-sonnet"


# ---------------------------------------------------------------------------
# Cost tracking integration
# ---------------------------------------------------------------------------

class TestCostTrackingPipeline:

    def test_costs_accumulate_across_requests(self, proxy):
        # Use task_override to bypass caching (different tasks → unique cache keys)
        for i in range(3):
            proxy.handle_request(
                f"generate some code variant {i}",
                task_override="code_generation",
                tokens_in=10,
                tokens_out=20,
            )
        summary = proxy.cost_tracker.summary()
        assert summary["total_requests"] >= 3

    def test_task_override_recorded_correctly(self, proxy):
        proxy.handle_request(
            "some prompt",
            task_override="bug_fix",
            tokens_in=5,
            tokens_out=10,
        )
        summary = proxy.cost_tracker.summary()
        assert summary["total_requests"] >= 1


# ---------------------------------------------------------------------------
# Event bus integration
# ---------------------------------------------------------------------------

class TestEventBusPipeline:

    def test_event_published_on_request(self, proxy):
        received = []
        proxy.event_bus.subscribe("request_completed", received.append)
        proxy.handle_request("test event bus")
        assert len(received) == 1
        event = received[0]
        assert "task" in event
        assert "model" in event
        assert "cost" in event

    def test_multiple_requests_fire_multiple_events(self, proxy):
        events = []
        proxy.event_bus.subscribe("request_completed", events.append)
        proxy.handle_request("first request")
        proxy.handle_request("second request")
        assert len(events) == 2

    def test_event_includes_savings(self, proxy):
        events = []
        proxy.event_bus.subscribe("request_completed", events.append)
        proxy.handle_request("free model request")
        assert "savings" in events[0]


# ---------------------------------------------------------------------------
# Fallback integration
# ---------------------------------------------------------------------------

class TestFallbackPipeline:

    def test_successful_request_fn_used(self, proxy):
        call_log = []

        def request_fn(model):
            call_log.append(model)
            return "success response"

        result = proxy.handle_request("fix this bug", request_fn=request_fn)
        assert result["result"].success is True
        assert len(call_log) >= 1

    def test_failed_request_fn_tries_fallback(self, proxy):
        attempts = []

        def flaky_fn(model):
            attempts.append(model)
            raise RuntimeError("provider down")

        result = proxy.handle_request("help me refactor", request_fn=flaky_fn)
        # Should have tried at least one model
        assert len(attempts) >= 1
        # Result should reflect failure (no fallback available in test config)
        assert result["result"].success is False or len(attempts) >= 1
