"""Embedding manager for Project Lodestar.

Handles conversion of text into vector embeddings.
"""

from typing import Any, Dict, List
import logging
import litellm

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """Manages text embedding generation.

    Args:
        config: Configuration for embeddings (model, dimension, etc.).
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.model = config.get("model", "text-embedding-3-small")
        self.dimensions = config.get("dimensions", 1536)

    def embed(self, text: str) -> List[float]:
        """Convert text into a vector embedding using LiteLLM.

        Args:
            text: The text to embed.

        Returns:
            List of floats representing the embedding.
        """
        try:
            response = litellm.embedding(
                model=self.model,
                input=[text]
            )
            return response.data[0]["embedding"]
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            # Return zero vector as fallback to avoid crashing (degraded mode)
            return [0.0] * self.dimensions

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Convert multiple texts into embeddings.

        Args:
            texts: List of strings to embed.

        Returns:
            List of embeddings.
        """
        try:
            response = litellm.embedding(
                model=self.model,
                input=texts
            )
            return [item["embedding"] for item in response.data]
        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            return [[0.0] * self.dimensions for _ in texts]
