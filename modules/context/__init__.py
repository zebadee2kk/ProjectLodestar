"""Context module for Project Lodestar.

Manages persistent session state and context assembly for AI tasks.
"""

from typing import Any, Dict, List, Optional
import logging
from modules.base import LodestarPlugin
from modules.context.session import SessionManager

logger = logging.getLogger(__name__)


class ContextModule(LodestarPlugin):
    """Manages project context and persistent sessions.

    Args:
        config: Module-specific configuration.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.session_manager = SessionManager(config.get("sessions", {}))

    def start(self) -> None:
        """Start the context module."""
        if not self.enabled:
            return
        logger.info("ContextModule started")

    def stop(self) -> None:
        """Gracefully stop the context module."""
        logger.info("ContextModule stopped")

    def health_check(self) -> Dict[str, Any]:
        """Check the health of the context module."""
        return {
            "status": "healthy" if self.enabled else "down",
            "module": "context",
        }

    def create_session(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new persistent session.

        Args:
            name: Descriptive name for the session.
            metadata: Additional session metadata.

        Returns:
            The unique session ID.
        """
        return self.session_manager.create_session(name, metadata)

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a session by ID."""
        return self.session_manager.get_session(session_id)

    def add_to_history(self, session_id: str, role: str, content: str) -> None:
        """Add a message to the session history.

        Args:
            session_id: The ID of the session.
            role: The role (e.g., 'user', 'assistant').
            content: The message content.
        """
        self.session_manager.append_history(session_id, role, content)

    def get_history(self, session_id: str, limit: int = 20) -> List[Dict[str, str]]:
        """Retrieve session history."""
        return self.session_manager.get_history(session_id, limit)
