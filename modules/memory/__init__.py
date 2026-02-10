"""Memory module for Project Lodestar.

Provides persistent vector storage and retrieval for AI context.
"""

from typing import Any, Dict, List, Optional
import logging

from modules.base import LodestarPlugin
from modules.memory.store import VectorStore
from modules.memory.embeddings import EmbeddingManager

logger = logging.getLogger(__name__)


class MemoryModule(LodestarPlugin):
    """Manages persistent project memory using vector embeddings.

    Args:
        config: Module-specific configuration.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.embedding_manager = EmbeddingManager(config.get("embeddings", {}))
        self.store = VectorStore(config.get("store", {}))

    def start(self) -> None:
        """Start the memory module and initialize connections."""
        if not self.enabled:
            return
        
        try:
            self.store.connect()
            logger.info("MemoryModule started and connected to vector store")
        except Exception as e:
            logger.error(f"Failed to start MemoryModule: {e}")
            self.enabled = False

    def stop(self) -> None:
        """Gracefully stop the memory module."""
        self.store.disconnect()
        logger.info("MemoryModule stopped")

    def health_check(self) -> Dict[str, Any]:
        """Check the health of the memory store."""
        status = "down"
        if self.enabled:
            store_health = self.store.health_check()
            status = store_health.get("status", "degraded")
        
        return {
            "status": status,
            "module": "memory",
            "store": self.store.__class__.__name__,
        }

    def remember(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store a piece of text as a vector embedding.

        Args:
            text: The text to store.
            metadata: Associated metadata.

        Returns:
            The ID of the stored vector.
        """
        vector = self.embedding_manager.embed(text)
        return self.store.upsert(vector, text, metadata)

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant memories.

        Args:
            query: The search query.
            limit: Maximum number of results.

        Returns:
            List of matching records with similarity scores.
        """
        vector = self.embedding_manager.embed(query)
        return self.store.search(vector, limit=limit)
