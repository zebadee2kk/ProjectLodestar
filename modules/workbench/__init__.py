"""Workbench module for Project Lodestar.

Unifies persistent memory, context management, and knowledge retrieval.
"""

from typing import Any, Dict, List, Optional
import logging
from modules.base import LodestarPlugin
from modules.workbench.orchestrator import WorkbenchOrchestrator

logger = logging.getLogger(__name__)


class WorkbenchModule(LodestarPlugin):
    """Main orchestrator for the AI project workbench.

    Args:
        config: Module-specific configuration.
    """

    def __init__(self, config: Dict[str, Any], proxy: Optional[Any] = None) -> None:
        super().__init__(config)
        self.orchestrator = WorkbenchOrchestrator(config, proxy=proxy)

    def start(self) -> None:
        """Start the workbench module."""
        if not self.enabled:
            return
        self.orchestrator.start()
        logger.info("WorkbenchModule started")

    def stop(self) -> None:
        """Gracefully stop the workbench module."""
        self.orchestrator.stop()
        logger.info("WorkbenchModule stopped")

    def health_check(self) -> Dict[str, Any]:
        """Check the health of the workbench module."""
        return {
            "status": "healthy" if self.enabled else "down",
            "module": "workbench",
            "orchestrator": self.orchestrator.health_check()
        }

    def chat(self, prompt: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Process a workbench chat request with persistent context and knowledge."""
        return self.orchestrator.process_request(prompt, session_id=session_id)
