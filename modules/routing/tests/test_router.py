"""Tests for the SemanticRouter."""

import pytest
from modules.routing.router import SemanticRouter, DEFAULT_ROUTING_RULES


@pytest.fixture
def router_config():
    """Standard enabled router config."""
    return {
        "enabled": True,
        "routing_rules": DEFAULT_ROUTING_RULES,
        "fallback_chains": {
            "claude-sonnet": ["gpt-4o-mini", "gpt-3.5-turbo"],
            "gpt-3.5-turbo": ["local-llama"],
        },
    }


@pytest.fixture
def router(router_config):
    """A started SemanticRouter instance."""
    r = SemanticRouter(router_config)
    r.start()
    return r


class TestSemanticRouterLifecycle:
    """Tests for start/stop/health_check."""

    def test_start_enabled(self, router_config):
        r = SemanticRouter(router_config)
        r.start()
        assert r._started is True

    def test_start_disabled(self):
        r = SemanticRouter({"enabled": False})
        r.start()
        assert r._started is False

    def test_stop(self, router):
        router.stop()
        assert router._started is False

    def test_health_check_started(self, router):
        health = router.health_check()
        assert health["status"] == "healthy"
        assert health["rules_count"] == len(DEFAULT_ROUTING_RULES)

    def test_health_check_stopped(self, router_config):
        r = SemanticRouter(router_config)
        health = r.health_check()
        assert health["status"] == "down"


class TestTaskClassification:
    """Tests for classify_task keyword matching."""

    def test_classify_bug_fix(self, router):
        assert router.classify_task("fix the login bug") == "bug_fix"

    def test_classify_code_review(self, router):
        assert router.classify_task("review this pull request") == "code_review"

    def test_classify_architecture(self, router):
        assert router.classify_task("design the system architecture") == "architecture"

    def test_classify_documentation(self, router):
        assert router.classify_task("write a readme document") == "documentation"

    def test_classify_refactor(self, router):
        assert router.classify_task("refactor the database layer") == "refactor"

    def test_classify_code_generation(self, router):
        assert router.classify_task("create a new user model") == "code_generation"

    def test_classify_general_fallback(self, router):
        assert router.classify_task("hello world") == "general"

    def test_classify_case_insensitive(self, router):
        assert router.classify_task("FIX THE BUG") == "bug_fix"


class TestRouting:
    """Tests for the route() method."""

    def test_route_uses_classification(self, router):
        model = router.route("fix the crash bug")
        assert model == "gpt-3.5-turbo"

    def test_route_architecture_to_claude(self, router):
        model = router.route("design the system architecture")
        assert model == "claude-sonnet"

    def test_route_with_task_override(self, router):
        model = router.route("anything here", task_override="code_review")
        assert model == "claude-sonnet"

    def test_route_unknown_task_uses_general(self, router):
        model = router.route("something random", task_override="unknown_task")
        assert model == "gpt-3.5-turbo"

    def test_route_defaults_to_free_model(self, router):
        model = router.route("do something")
        assert model == "gpt-3.5-turbo"


class TestFallbackChains:
    """Tests for fallback chain retrieval."""

    def test_get_fallback_chain(self, router):
        chain = router.get_fallback_chain("claude-sonnet")
        assert chain == ["gpt-4o-mini", "gpt-3.5-turbo"]

    def test_get_fallback_chain_missing(self, router):
        chain = router.get_fallback_chain("nonexistent-model")
        assert chain == []

    def test_fallback_chain_preserves_order(self, router):
        chain = router.get_fallback_chain("claude-sonnet")
        assert chain[0] == "gpt-4o-mini"
        assert chain[1] == "gpt-3.5-turbo"
