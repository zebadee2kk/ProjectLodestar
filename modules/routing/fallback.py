"""Fallback chain executor for graceful degradation.

When a model request fails, automatically retries with the next
model in the configured fallback chain before giving up.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class RequestResult:
    """Result of a model request attempt.

    Attributes:
        success: Whether the request succeeded.
        model: The model that was used.
        response: The response data on success, or None.
        error: The error message on failure, or None.
        attempts: List of (model, error) tuples for all failed attempts.
    """

    success: bool
    model: str
    response: Any = None
    error: Optional[str] = None
    attempts: List[tuple] = None

    def __post_init__(self):
        if self.attempts is None:
            self.attempts = []


class FallbackExecutor:
    """Executes requests with automatic fallback on failure.

    Given a primary model and its fallback chain, tries each model
    in order until one succeeds or all have been exhausted.
    """

    def execute(
        self,
        primary_model: str,
        fallback_chain: List[str],
        request_fn: Callable[[str], Any],
    ) -> RequestResult:
        """Execute a request with fallback chain.

        Args:
            primary_model: First model to try.
            fallback_chain: Ordered list of fallback model aliases.
            request_fn: Callable that takes a model alias and returns
                        a response. Must raise an exception on failure.

        Returns:
            RequestResult with the outcome.
        """
        models_to_try = [primary_model] + fallback_chain
        attempts = []

        for model in models_to_try:
            try:
                response = request_fn(model)
                logger.info("Request succeeded with model '%s'", model)
                return RequestResult(
                    success=True,
                    model=model,
                    response=response,
                    attempts=attempts,
                )
            except Exception as exc:
                error_msg = str(exc)
                attempts.append((model, error_msg))
                logger.warning(
                    "Model '%s' failed: %s. Trying next fallback.",
                    model,
                    error_msg,
                )

        # All models exhausted
        logger.error(
            "All models failed after %d attempts: %s",
            len(attempts),
            [a[0] for a in attempts],
        )
        return RequestResult(
            success=False,
            model=primary_model,
            error=f"All {len(attempts)} models failed",
            attempts=attempts,
        )
