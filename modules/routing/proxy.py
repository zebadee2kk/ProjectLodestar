"""LiteLLM proxy integration layer.

Bridges the SemanticRouter with LiteLLM's proxy server by providing
custom callbacks that intercept requests, classify tasks, and record
costs — all without modifying LiteLLM's core behaviour.
"""

from typing import Any, Dict, List, Optional
import logging
import yaml
from pathlib import Path

from modules.base import EventBus
from modules.routing.router import SemanticRouter
from modules.routing.fallback import FallbackExecutor, RequestResult
from modules.costs.tracker import CostTracker

logger = logging.getLogger(__name__)


class LodestarProxy:
    """Orchestrates routing, fallback, and cost tracking for LLM requests.

    This is the main integration point between Lodestar's modules and
    the LiteLLM router. It reads module configs, initialises the router
    and cost tracker, and provides a single `handle_request` method that
    does classification -> routing -> fallback -> cost recording.

    Args:
        config_dir: Path to the config/ directory containing modules.yaml
                    and per-module configs.
        event_bus: Optional shared EventBus instance.
    """

    def __init__(
        self,
        config_dir: str = "config",
        event_bus: Optional[EventBus] = None,
    ) -> None:
        self.config_dir = Path(config_dir)
        self.event_bus = event_bus or EventBus()
        self._load_configs()

        self.router = SemanticRouter(self._routing_config)
        self.cost_tracker = CostTracker(self._costs_config)
        self.fallback_executor = FallbackExecutor()
        
        # Initialize Cache
        from modules.routing.cache import CacheManager
        self.cache = CacheManager()

    def _load_configs(self) -> None:
        """Load module configurations from YAML files."""
        modules_yaml = self.config_dir / "modules.yaml"
        if modules_yaml.exists():
            with open(modules_yaml) as f:
                self._modules_config = yaml.safe_load(f) or {}
        else:
            self._modules_config = {}

        routing_yaml = self.config_dir.parent / "modules" / "routing" / "config.yaml"
        if routing_yaml.exists():
            with open(routing_yaml) as f:
                raw = yaml.safe_load(f) or {}
                self._routing_config = raw.get("routing", {"enabled": True})
        else:
            self._routing_config = {"enabled": True}

        costs_yaml = self.config_dir.parent / "modules" / "costs" / "config.yaml"
        if costs_yaml.exists():
            with open(costs_yaml) as f:
                raw = yaml.safe_load(f) or {}
                self._costs_config = raw.get("costs", {"enabled": True})
        else:
            self._costs_config = {"enabled": True}

    def start(self) -> None:
        """Start all modules."""
        self.router.start()
        self.cost_tracker.start()
        logger.info("LodestarProxy started")

    def stop(self) -> None:
        """Stop all modules gracefully."""
        self.router.stop()
        self.cost_tracker.stop()
        logger.info("LodestarProxy stopped")

    def handle_request(
        self,
        prompt: str,
        request_fn: Any = None,
        task_override: Optional[str] = None,
        model_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process an LLM request through the full pipeline.

        1. Classify the task (or use override)
        2. Route to best model (or use override)
        3. Execute with fallback chain
        4. Record cost
        5. Publish event

        Args:
            prompt: The user's input prompt.
            request_fn: Callable(model) -> response. If None, returns
                        routing decision only (dry-run mode).
            task_override: Force a specific task classification.
            model_override: Force a specific model (bypasses routing).

        Returns:
            Dict with task, model, result, cost_entry keys.
        """
        # Step 1: Classify
        task = task_override or self.router.classify_task(prompt)

        # Step 1.5: Check Cache (if no overrides)
        if not task_override and not model_override:
            cached_response = self.cache.get(model="routeless", messages=[{"role": "user", "content": prompt}])
            if cached_response:
                logger.info("Serving from cache")
                return cached_response

        # Step 2: Route
        model = model_override or self.router.route(prompt, task_override=task)

        # Step 3: Execute (or dry-run)
        if request_fn is not None:
            fallback_chain = self.router.get_fallback_chain(model)
            result = self.fallback_executor.execute(
                model, fallback_chain, request_fn
            )
            actual_model = result.model if result.success else model
        else:
            result = RequestResult(success=True, model=model, response=None)
            actual_model = model

        # Step 4: Record cost (estimate with zero tokens in dry-run)
        cost_entry = self.cost_tracker.record(
            model=actual_model,
            tokens_in=0,
            tokens_out=0,
            task=task,
        )

        # Step 5: Publish event
        event_data = {
            "task": task,
            "model": actual_model,
            "success": result.success,
            "cost": cost_entry["cost"],
            "savings": cost_entry["savings"],
        }
        self.event_bus.publish("request_completed", event_data)

        result_dict = {
            "task": task,
            "model": actual_model,
            "result": result,
            "cost_entry": cost_entry,
        }
        
        # Step 6: Cache success (store serializable data only)
        if result.success and not task_override and not model_override:
            cacheable_data = {
                "task": task,
                "model": actual_model,
                "cost_entry": cost_entry,
                # Don't cache the full RequestResult, just the essential info
                "success": True,
            }
            self.cache.set(
                model="routeless", 
                messages=[{"role": "user", "content": prompt}], 
                response=cacheable_data
            )
            
        return result_dict

    def health_check(self) -> Dict[str, Any]:
        """Return health status of all modules."""
        return {
            "proxy": "healthy",
            "router": self.router.health_check(),
            "cost_tracker": self.cost_tracker.health_check(),
        }
