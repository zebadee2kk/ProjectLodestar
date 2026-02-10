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
from modules.health.checker import HealthChecker
from modules.workbench import WorkbenchModule

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
        self.health_checker = HealthChecker(self._health_config, self.event_bus)
        self.fallback_executor = FallbackExecutor()
        
        # Initialize Cache
        from modules.routing.cache import CacheManager
        self.cache = CacheManager()

        # Initialize Workbench
        self.workbench = WorkbenchModule(self._modules_config.get("workbench", {}), proxy=self)

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

        health_yaml = self.config_dir.parent / "modules" / "health" / "config.yaml"
        if health_yaml.exists():
            with open(health_yaml) as f:
                raw = yaml.safe_load(f) or {}
                self._health_config = raw.get("health", {"enabled": True})
        else:
            self._health_config = {"enabled": True}

        # Load local overrides from .lodestar/config.yaml
        local_config_path = Path(".lodestar/config.yaml")
        if local_config_path.exists():
            try:
                with open(local_config_path) as f:
                    local_overrides = yaml.safe_load(f) or {}
                
                # Merge overrides into class attributes
                if "routing" in local_overrides:
                    self._routing_config.update(local_overrides["routing"])
                if "costs" in local_overrides:
                    self._costs_config.update(local_overrides["costs"])
                if "health" in local_overrides:
                    self._health_config.update(local_overrides["health"])
                
                logger.debug(f"Loaded local overrides from {local_config_path}")
            except Exception as e:
                logger.error(f"Error loading local overrides: {e}")


    def start(self) -> None:
        """Start all modules."""
        self.router.start()
        self.cost_tracker.start()
        self.health_checker.start()
        self.workbench.start()
        logger.info("LodestarProxy started")

    def stop(self) -> None:
        """Stop all modules gracefully."""
        self.router.stop()
        self.cost_tracker.stop()
        self.health_checker.stop()
        self.workbench.stop()
        logger.info("LodestarProxy stopped")

    def handle_request(
        self,
        prompt: str,
        request_fn: Any = None,
        task_override: Optional[str] = None,
        model_override: Optional[str] = None,
        tokens_in: int = 0,
        tokens_out: int = 0,
        live: bool = False,
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
            tokens_in: Input token count (from LiteLLM callback).
            tokens_out: Output token count (from LiteLLM callback).
            live: If True and request_fn is None, uses internal live requester.

        Returns:
            Dict with task, model, result, cost_entry keys.
        """
        # Step 1: Classify
        task = task_override or self.router.classify_task(prompt)

        # Step 2: Route
        model = model_override or self.router.route(prompt, task_override=task)

        # Step 2.5: Check Cache (after routing so we have the model for the key)
        if not task_override and not model_override:
            cached_response = self.cache.get(model=model, messages=[{"role": "user", "content": prompt}])
            if cached_response:
                logger.info("Serving from cache")
                return cached_response

        # Step 3: Execute (or dry-run)
        executor_fn = request_fn
        if executor_fn is None and live:
            executor_fn = self._get_live_request_fn(prompt)

        if executor_fn is not None:
            fallback_chain = self.router.get_fallback_chain(model)
            result = self.fallback_executor.execute(
                model, fallback_chain, executor_fn
            )
            actual_model = result.model if result.success else model
        else:
            result = RequestResult(success=True, model=model, response=None)
            actual_model = model

        # Step 4: Record cost
        # If we had a real execution, we might get tokens from the result
        t_in = tokens_in
        t_out = tokens_out
        if result.success and result.response and hasattr(result.response, "usage"):
            t_in = result.response.usage.prompt_tokens
            t_out = result.response.usage.completion_tokens

        cost_entry = self.cost_tracker.record(
            model=actual_model,
            tokens_in=t_in,
            tokens_out=t_out,
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
                model=actual_model,
                messages=[{"role": "user", "content": prompt}],
                response=cacheable_data
            )
            
        return result_dict

    def _get_live_request_fn(self, prompt: str) -> Any:
        """Create a request function that calls the local LiteLLM router."""
        import litellm

        def live_request(model_name: str) -> Any:
            return litellm.completion(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                api_base="http://localhost:4000",
                api_key="sk-dummy"
            )

        return live_request

    def health_check(self) -> Dict[str, Any]:
        """Return health status of all modules."""
        return {
            "proxy": "healthy",
            "router": self.router.health_check(),
            "cost_tracker": self.cost_tracker.health_check(),
            "health_checker": self.health_checker.health_check(),
            "workbench": self.workbench.health_check(),
        }
