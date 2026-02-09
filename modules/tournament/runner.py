"""Model tournament runner for side-by-side comparison.

Runs the same prompt against multiple models and collects results
for comparison. Tracks historical matches and maintains a leaderboard.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
import logging
import time

from modules.base import LodestarPlugin

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    """Result from a single model in a tournament match.

    Attributes:
        model: Model alias that was called.
        response: The model's response text, or None on failure.
        latency_ms: Time taken in milliseconds.
        success: Whether the call succeeded.
        error: Error message if the call failed.
    """
    model: str
    response: Optional[str]
    latency_ms: float
    success: bool
    error: Optional[str] = None


@dataclass
class TournamentResult:
    """Result of a full tournament match across multiple models.

    Attributes:
        prompt: The prompt sent to all models.
        matches: Per-model results.
        winner: Winning model alias (set after voting).
        timestamp: ISO timestamp of the match.
    """
    prompt: str
    matches: List[MatchResult]
    winner: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class TournamentRunner(LodestarPlugin):
    """Runs side-by-side model comparisons.

    Sends the same prompt to multiple models, collects responses with
    timing data, and maintains a win/loss leaderboard across matches.

    Args:
        config: Tournament configuration dict.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.default_models: List[str] = config.get(
            "default_models", ["gpt-3.5-turbo", "local-llama"]
        )
        self.max_models: int = config.get("max_models_per_match", 4)
        self._history: List[TournamentResult] = []
        self._leaderboard: Dict[str, Dict[str, int]] = {}
        self._started = False

    def start(self) -> None:
        """Start the tournament runner."""
        if not self.enabled:
            logger.info("Tournament runner disabled, skipping start")
            return
        self._started = True
        logger.info("Tournament runner started")

    def stop(self) -> None:
        """Stop the tournament runner."""
        self._started = False
        logger.info("Tournament runner stopped")

    def health_check(self) -> Dict[str, Any]:
        """Return tournament runner health status."""
        return {
            "status": "healthy" if self._started else "down",
            "enabled": self.enabled,
            "matches_run": len(self._history),
            "models_tracked": len(self._leaderboard),
        }

    def run_match(
        self,
        prompt: str,
        request_fn: Callable[[str, str], str],
        models: Optional[List[str]] = None,
    ) -> TournamentResult:
        """Run a tournament match: same prompt against multiple models.

        Args:
            prompt: The prompt to send to each model.
            request_fn: Callable(model, prompt) -> response string.
                        Must raise on failure.
            models: Models to compare. Defaults to default_models.

        Returns:
            TournamentResult with per-model MatchResults.
        """
        models = (models or self.default_models)[:self.max_models]
        if len(models) < 2:
            raise ValueError("Tournament requires at least 2 models")

        matches: List[MatchResult] = []
        for model in models:
            start_time = time.monotonic()
            try:
                response = request_fn(model, prompt)
                elapsed = (time.monotonic() - start_time) * 1000
                matches.append(MatchResult(
                    model=model,
                    response=str(response),
                    latency_ms=round(elapsed, 1),
                    success=True,
                ))
            except Exception as exc:
                elapsed = (time.monotonic() - start_time) * 1000
                matches.append(MatchResult(
                    model=model,
                    response=None,
                    latency_ms=round(elapsed, 1),
                    success=False,
                    error=str(exc),
                ))
                logger.warning("Model %s failed in tournament: %s", model, exc)

        result = TournamentResult(prompt=prompt, matches=matches)
        self._history.append(result)
        return result

    def vote(self, result: TournamentResult, winner: str) -> None:
        """Record a vote for the winning model in a match.

        Args:
            result: The TournamentResult to record the vote for.
            winner: Model alias of the winner.

        Raises:
            ValueError: If winner wasn't a participant in the match.
        """
        participants = [m.model for m in result.matches if m.success]
        if winner not in participants:
            raise ValueError(
                f"Winner '{winner}' not in successful participants: {participants}"
            )

        result.winner = winner

        # Update leaderboard
        for match in result.matches:
            if not match.success:
                continue
            if match.model not in self._leaderboard:
                self._leaderboard[match.model] = {"wins": 0, "losses": 0, "draws": 0}
            if match.model == winner:
                self._leaderboard[match.model]["wins"] += 1
            else:
                self._leaderboard[match.model]["losses"] += 1

    def draw(self, result: TournamentResult) -> None:
        """Record a draw for a match (no winner).

        Args:
            result: The TournamentResult to record as a draw.
        """
        result.winner = "draw"
        for match in result.matches:
            if not match.success:
                continue
            if match.model not in self._leaderboard:
                self._leaderboard[match.model] = {"wins": 0, "losses": 0, "draws": 0}
            self._leaderboard[match.model]["draws"] += 1

    def leaderboard(self) -> Dict[str, Dict[str, Any]]:
        """Get the current leaderboard with win rates.

        Returns:
            Dict of model -> {wins, losses, draws, win_rate}.
        """
        board = {}
        for model, stats in self._leaderboard.items():
            total = stats["wins"] + stats["losses"] + stats["draws"]
            win_rate = round(stats["wins"] / total * 100, 1) if total > 0 else 0.0
            board[model] = {**stats, "total": total, "win_rate": win_rate}
        return board

    def history(self) -> List[TournamentResult]:
        """Get all historical tournament results."""
        return list(self._history)

    def format_match(self, result: TournamentResult) -> str:
        """Format a tournament result for terminal display.

        Args:
            result: The TournamentResult to format.

        Returns:
            Formatted string for CLI output.
        """
        lines = [
            "=" * 60,
            f"Tournament Match — {result.timestamp[:19]}",
            f"Prompt: {result.prompt[:80]}{'...' if len(result.prompt) > 80 else ''}",
            "-" * 60,
        ]
        for i, match in enumerate(result.matches, 1):
            status = "OK" if match.success else "FAIL"
            lines.append(f"  [{i}] {match.model} ({status}, {match.latency_ms:.0f}ms)")
            if match.success:
                preview = match.response[:120] if match.response else ""
                lines.append(f"      {preview}{'...' if len(match.response or '') > 120 else ''}")
            else:
                lines.append(f"      Error: {match.error}")
        lines.append("-" * 60)
        if result.winner:
            lines.append(f"Winner: {result.winner}")
        else:
            lines.append("Winner: (not yet voted)")
        lines.append("=" * 60)
        return "\n".join(lines)
