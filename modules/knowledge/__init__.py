"""Knowledge module for Project Lodestar.

Handles repository indexing and semantic search across code and docs.
"""

from typing import Any, Dict, List, Optional
import logging
from modules.base import LodestarPlugin
from modules.knowledge.indexer import RepositoryIndexer

logger = logging.getLogger(__name__)


class KnowledgeModule(LodestarPlugin):
    """Manages project knowledge and semantic search.

    Args:
        config: Module-specific configuration.
    """

    def __init__(self, config: Dict[str, Any], memory_module: Optional[Any] = None) -> None:
        super().__init__(config)
        self.indexer = RepositoryIndexer(config.get("indexer", {}), memory_module=memory_module)

    def start(self) -> None:
        """Start the knowledge module."""
        if not self.enabled:
            return
        logger.info("KnowledgeModule started")

    def stop(self) -> None:
        """Gracefully stop the knowledge module."""
        logger.info("KnowledgeModule stopped")

    def health_check(self) -> Dict[str, Any]:
        """Check the health of the knowledge module."""
        return {
            "status": "healthy" if self.enabled else "down",
            "module": "knowledge",
        }

    def index_repository(self, path: str) -> Dict[str, Any]:
        """Index the entire repository.

        Args:
            path: Root path of the repository.

        Returns:
            Summary of indexing results (files indexed, errors, etc.).
        """
        return self.indexer.index_all(path)

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search across indexed knowledge."""
        # This will delegate to the memory module's vector store 
        # but specifically targeting the 'knowledge' collection if separated,
        # or filtered by metadata in a shared collection.
        return self.indexer.search(query, limit)
