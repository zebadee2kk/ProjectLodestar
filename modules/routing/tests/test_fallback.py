"""Tests for the fallback chain executor."""

import pytest
from modules.routing.fallback import FallbackExecutor, RequestResult


@pytest.fixture
def executor():
    return FallbackExecutor()


class TestRequestResult:

    def test_default_attempts_empty(self):
        r = RequestResult(success=True, model="m")
        assert r.attempts == []

    def test_success_result(self):
        r = RequestResult(success=True, model="m", response="data")
        assert r.success is True
        assert r.response == "data"

    def test_failure_result(self):
        r = RequestResult(success=False, model="m", error="timeout")
        assert r.success is False
        assert r.error == "timeout"


class TestFallbackExecutor:

    def test_primary_succeeds(self, executor):
        result = executor.execute(
            "model-a", ["model-b"], lambda m: f"response from {m}"
        )
        assert result.success is True
        assert result.model == "model-a"
        assert result.response == "response from model-a"
        assert result.attempts == []

    def test_primary_fails_fallback_succeeds(self, executor):
        call_count = 0

        def request_fn(model):
            nonlocal call_count
            call_count += 1
            if model == "model-a":
                raise ConnectionError("model-a down")
            return f"response from {model}"

        result = executor.execute(
            "model-a", ["model-b"], request_fn
        )
        assert result.success is True
        assert result.model == "model-b"
        assert len(result.attempts) == 1
        assert result.attempts[0][0] == "model-a"

    def test_all_models_fail(self, executor):
        def always_fail(model):
            raise RuntimeError(f"{model} error")

        result = executor.execute(
            "model-a", ["model-b", "model-c"], always_fail
        )
        assert result.success is False
        assert len(result.attempts) == 3
        assert "All 3 models failed" in result.error

    def test_no_fallback_chain(self, executor):
        result = executor.execute(
            "model-a", [], lambda m: "ok"
        )
        assert result.success is True
        assert result.model == "model-a"

    def test_no_fallback_and_fail(self, executor):
        def fail(model):
            raise RuntimeError("down")

        result = executor.execute("model-a", [], fail)
        assert result.success is False
        assert len(result.attempts) == 1

    def test_fallback_preserves_order(self, executor):
        models_tried = []

        def track_and_fail(model):
            models_tried.append(model)
            raise RuntimeError("fail")

        executor.execute(
            "first", ["second", "third"], track_and_fail
        )
        assert models_tried == ["first", "second", "third"]

    def test_second_fallback_succeeds(self, executor):
        def fail_first_two(model):
            if model in ("a", "b"):
                raise RuntimeError("nope")
            return "ok"

        result = executor.execute("a", ["b", "c"], fail_first_two)
        assert result.success is True
        assert result.model == "c"
        assert len(result.attempts) == 2
