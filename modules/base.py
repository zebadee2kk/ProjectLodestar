"""
Base infrastructure for ProjectLodestar v2 modules.

Provides the LodestarPlugin abstract base class that all modules must
implement, and an EventBus for decoupled inter-module communication.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List
import logging

logger = logging.getLogger(__name__)


class LodestarPlugin(ABC):
    """Abstract base class for all Lodestar modules.

    Every v2 module must subclass this and implement start(), stop(),
    and health_check(). Modules are independently enabled/disabled
    via config and must never depend on other modules.

    Args:
        config: Module-specific configuration dictionary.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.enabled = config.get("enabled", False)

    @abstractmethod
    def start(self) -> None:
        """Start the module. Called when module is enabled."""

    @abstractmethod
    def stop(self) -> None:
        """Stop the module gracefully, releasing resources."""

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Return module health status.

        Returns:
            Dict with at least 'status' key ('healthy', 'degraded', or 'down')
            and any module-specific metrics.
        """


class EventBus:
    """Publish-subscribe event system for decoupled module communication.

    Modules publish events (e.g. 'request_completed') and other modules
    subscribe to react without direct dependencies.
    """

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[..., None]]] = {}

    def subscribe(self, event: str, callback: Callable[..., None]) -> None:
        """Register a callback for an event type.

        Args:
            event: Event name to subscribe to.
            callback: Function to call when event is published.
        """
        if event not in self._subscribers:
            self._subscribers[event] = []
        self._subscribers[event].append(callback)

    def unsubscribe(self, event: str, callback: Callable[..., None]) -> None:
        """Remove a callback from an event type.

        Args:
            event: Event name to unsubscribe from.
            callback: Function to remove.
        """
        if event in self._subscribers:
            self._subscribers[event] = [
                cb for cb in self._subscribers[event] if cb is not callback
            ]

    def publish(self, event: str, data: Any = None) -> None:
        """Publish an event to all subscribers.

        Errors in individual callbacks are logged but do not prevent
        other subscribers from receiving the event.

        Args:
            event: Event name to publish.
            data: Arbitrary data payload for subscribers.
        """
        for callback in self._subscribers.get(event, []):
            try:
                callback(data)
            except Exception:
                logger.exception(
                    "Error in event subscriber for '%s'", event
                )
