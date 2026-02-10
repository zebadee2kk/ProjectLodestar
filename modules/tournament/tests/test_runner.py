"""Tests for the TournamentRunner."""

import pytest
from modules.tournament.runner import TournamentRunner, MatchResult, TournamentResult


@pytest.fixture
def tournament_config():
    return {
        "enabled": True,
        "default_models": ["model-a", "model-b"],
        "max_models_per_match": 4,
    }


@pytest.fixture
def runner(tournament_config):
    t = TournamentRunner(tournament_config)
    t.start()
    return t


def mock_request_fn(model, prompt):
    """Simple mock that returns a string response."""
    return f"Response from {model}: {prompt}"


def flaky_request_fn(model, prompt):
    """Mock where model-b fails."""
    if model == "model-b":
        raise ConnectionError("model-b is down")
    return f"Response from {model}"


class TestLifecycle:

    def test_start_enabled(self, tournament_config):
        t = TournamentRunner(tournament_config)
        t.start()
        assert t._started is True

    def test_start_disabled(self):
        t = TournamentRunner({"enabled": False})
        t.start()
        assert t._started is False

    def test_stop(self, runner):
        runner.stop()
        assert runner._started is False

    def test_health_check(self, runner):
        health = runner.health_check()
        assert health["status"] == "healthy"
        assert health["matches_run"] == 0
        assert health["models_tracked"] == 0

    def test_health_check_down(self, tournament_config):
        t = TournamentRunner(tournament_config)
        assert t.health_check()["status"] == "down"


class TestRunMatch:

    def test_basic_match(self, runner):
        result = runner.run_match("test prompt", mock_request_fn)
        assert len(result.matches) == 2
        assert all(m.success for m in result.matches)
        assert result.winner is None

    def test_responses_captured(self, runner):
        result = runner.run_match("hello world", mock_request_fn)
        assert "model-a" in result.matches[0].response
        assert "model-b" in result.matches[1].response

    def test_latency_recorded(self, runner):
        result = runner.run_match("test", mock_request_fn)
        for match in result.matches:
            assert match.latency_ms >= 0

    def test_custom_models(self, runner):
        result = runner.run_match(
            "test", mock_request_fn,
            models=["x", "y", "z"]
        )
        assert len(result.matches) == 3
        assert result.matches[0].model == "x"

    def test_max_models_enforced(self, runner):
        result = runner.run_match(
            "test", mock_request_fn,
            models=["a", "b", "c", "d", "e"]
        )
        assert len(result.matches) == 4  # max_models_per_match

    def test_failed_model(self, runner):
        result = runner.run_match("test", flaky_request_fn)
        assert result.matches[0].success is True
        assert result.matches[1].success is False
        assert result.matches[1].error == "model-b is down"

    def test_match_added_to_history(self, runner):
        runner.run_match("prompt 1", mock_request_fn)
        runner.run_match("prompt 2", mock_request_fn)
        assert len(runner.history()) == 2

    def test_requires_two_models(self, runner):
        with pytest.raises(ValueError, match="at least 2 models"):
            runner.run_match("test", mock_request_fn, models=["solo"])

    def test_prompt_stored(self, runner):
        result = runner.run_match("my specific prompt", mock_request_fn)
        assert result.prompt == "my specific prompt"

    def test_timestamp_set(self, runner):
        result = runner.run_match("test", mock_request_fn)
        assert result.timestamp is not None
        assert len(result.timestamp) > 10


class TestVoting:

    def test_vote_sets_winner(self, runner):
        result = runner.run_match("test", mock_request_fn)
        runner.vote(result, "model-a")
        assert result.winner == "model-a"

    def test_vote_updates_leaderboard(self, runner):
        result = runner.run_match("test", mock_request_fn)
        runner.vote(result, "model-a")
        board = runner.leaderboard()
        assert board["model-a"]["wins"] == 1
        assert board["model-b"]["losses"] == 1

    def test_vote_invalid_winner(self, runner):
        result = runner.run_match("test", mock_request_fn)
        with pytest.raises(ValueError, match="not in successful participants"):
            runner.vote(result, "nonexistent-model")

    def test_vote_failed_model_not_eligible(self, runner):
        result = runner.run_match("test", flaky_request_fn)
        with pytest.raises(ValueError, match="not in successful participants"):
            runner.vote(result, "model-b")

    def test_multiple_votes_accumulate(self, runner):
        for _ in range(3):
            result = runner.run_match("test", mock_request_fn)
            runner.vote(result, "model-a")
        board = runner.leaderboard()
        assert board["model-a"]["wins"] == 3
        assert board["model-b"]["losses"] == 3


class TestDraw:

    def test_draw_sets_winner_to_draw(self, runner):
        result = runner.run_match("test", mock_request_fn)
        runner.draw(result)
        assert result.winner == "draw"

    def test_draw_updates_leaderboard(self, runner):
        result = runner.run_match("test", mock_request_fn)
        runner.draw(result)
        board = runner.leaderboard()
        assert board["model-a"]["draws"] == 1
        assert board["model-b"]["draws"] == 1


class TestLeaderboard:

    def test_empty_leaderboard(self, runner):
        assert runner.leaderboard() == {}

    def test_win_rate_calculation(self, runner):
        # model-a wins 2, model-b wins 1
        for _ in range(2):
            result = runner.run_match("test", mock_request_fn)
            runner.vote(result, "model-a")
        result = runner.run_match("test", mock_request_fn)
        runner.vote(result, "model-b")

        board = runner.leaderboard()
        assert board["model-a"]["win_rate"] == pytest.approx(66.7, abs=0.1)
        assert board["model-b"]["win_rate"] == pytest.approx(33.3, abs=0.1)


class TestFormatMatch:

    def test_format_contains_models(self, runner):
        result = runner.run_match("test", mock_request_fn)
        output = runner.format_match(result)
        assert "model-a" in output
        assert "model-b" in output
        assert "Tournament Match" in output

    def test_format_shows_winner(self, runner):
        result = runner.run_match("test", mock_request_fn)
        runner.vote(result, "model-a")
        output = runner.format_match(result)
        assert "Winner: model-a" in output

    def test_format_shows_failure(self, runner):
        result = runner.run_match("test", flaky_request_fn)
        output = runner.format_match(result)
        assert "FAIL" in output
        assert "model-b is down" in output

    def test_format_no_winner_yet(self, runner):
        result = runner.run_match("test", mock_request_fn)
        output = runner.format_match(result)
        assert "not yet voted" in output

    def test_format_long_prompt_truncated(self, runner):
        long_prompt = "x" * 200
        result = runner.run_match(long_prompt, mock_request_fn)
        output = runner.format_match(result)
        assert "..." in output

    def test_format_shows_latency(self, runner):
        result = runner.run_match("test", mock_request_fn)
        output = runner.format_match(result)
        assert "ms" in output


class TestTournamentEdgeCases:

    def test_all_models_fail(self, runner):
        def all_fail(model, prompt):
            raise RuntimeError(f"{model} crashed")

        result = runner.run_match("test", all_fail)
        assert all(not m.success for m in result.matches)
        assert all(m.error is not None for m in result.matches)

    def test_vote_on_all_failed_match(self, runner):
        def all_fail(model, prompt):
            raise RuntimeError("down")

        result = runner.run_match("test", all_fail)
        with pytest.raises(ValueError, match="not in successful participants"):
            runner.vote(result, "model-a")

    def test_revote_overwrites_winner(self, runner):
        result = runner.run_match("test", mock_request_fn)
        runner.vote(result, "model-a")
        assert result.winner == "model-a"
        runner.vote(result, "model-b")
        assert result.winner == "model-b"

    def test_draw_after_vote(self, runner):
        result = runner.run_match("test", mock_request_fn)
        runner.vote(result, "model-a")
        runner.draw(result)
        assert result.winner == "draw"

    def test_request_fn_returns_none(self, runner):
        result = runner.run_match("test", lambda m, p: None)
        # None is coerced to string "None"
        assert result.matches[0].success is True
        assert result.matches[0].response == "None"

    def test_request_fn_returns_empty_string(self, runner):
        result = runner.run_match("test", lambda m, p: "")
        assert result.matches[0].success is True
        assert result.matches[0].response == ""

    def test_draw_affects_leaderboard(self, runner):
        """Draws should count in total matches, reducing win rate."""
        result = runner.run_match("test", mock_request_fn)
        runner.vote(result, "model-a")
        result2 = runner.run_match("test", mock_request_fn)
        runner.draw(result2)
        board = runner.leaderboard()
        # model-a: 1 win, 0 loss, 1 draw = 50% win rate
        assert board["model-a"]["win_rate"] == 50.0

    def test_health_check_after_matches(self, runner):
        runner.run_match("test", mock_request_fn)
        runner.vote(runner.history()[0], "model-a")
        health = runner.health_check()
        assert health["matches_run"] == 1
        assert health["models_tracked"] == 2

    def test_history_returns_copy(self, runner):
        runner.run_match("test", mock_request_fn)
        history = runner.history()
        history.clear()
        assert len(runner.history()) == 1  # original unchanged

    def test_match_result_dataclass(self):
        m = MatchResult(model="test", response="ok", latency_ms=42.5, success=True)
        assert m.model == "test"
        assert m.latency_ms == 42.5
        assert m.error is None

    def test_tournament_result_dataclass(self):
        r = TournamentResult(prompt="test", matches=[])
        assert r.winner is None
        assert r.timestamp is not None
