"""Vector store abstraction and implementations for Project Lodestar.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import logging
import uuid

import qdrant_client
from qdrant_client.http import models as qmodels

logger = logging.getLogger(__name__)


class BaseVectorStore(ABC):
    """Abstract base class for vector stores."""

    @abstractmethod
    def connect(self) -> None:
        """Connect to the store."""

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the store."""

    @abstractmethod
    def upsert(self, vector: List[float], text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Insert or update a vector record."""

    @abstractmethod
    def search(self, vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar vectors."""

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Check store health."""


class VectorStore(BaseVectorStore):
    """Qdrant implementation of the vector store.

    Defaults to a local in-memory/file-based Qdrant if no URL is provided.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.url = config.get("url", "http://localhost:6333")
        self.path = config.get("path", ".lodestar/memory.db")
        self.collection_name = config.get("collection", "lodestar_memories")
        self.vector_size = config.get("vector_size", 1536)
        self.client: Optional[qdrant_client.QdrantClient] = None

    def connect(self) -> None:
        """Initialize connection to Qdrant."""
        if self.url:
            try:
                self.client = qdrant_client.QdrantClient(url=self.url)
                # Try to ping
                self.client.get_collections()
            except Exception:
                logger.warning(f"Could not connect to Qdrant at {self.url}, falling back to local file {self.path}")
                self.client = qdrant_client.QdrantClient(path=self.path)
        else:
            self.client = qdrant_client.QdrantClient(path=self.path)

        # Create collection if it doesn't exist
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        
        if not exists:
            logger.info(f"Creating Qdrant collection: {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=qmodels.VectorParams(
                    size=self.vector_size,
                    distance=qmodels.Distance.COSINE
                )
            )

    def disconnect(self) -> None:
        """Close connection."""
        self.client = None

    def upsert(self, vector: List[float], text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store vector and text in Qdrant."""
        if not self.client:
            self.connect()
        
        point_id = str(uuid.uuid4())
        payload = metadata or {}
        payload["text"] = text
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                qmodels.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload
                )
            ]
        )
        return point_id

    def search(self, vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """Find similar vectors in Qdrant."""
        if not self.client:
            self.connect()
            
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            limit=limit
        )
        
        return [
            {
                "id": r.id,
                "score": r.score,
                "text": r.payload.get("text", ""),
                "metadata": {k: v for k, v in r.payload.items() if k != "text"}
            }
            for r in results
        ]

    def health_check(self) -> Dict[str, Any]:
        """Verify Qdrant connectivity."""
        try:
            if not self.client:
                return {"status": "down", "error": "Not connected"}
            
            self.client.get_collections()
            return {"status": "healthy", "type": "qdrant"}
        except Exception as e:
            return {"status": "down", "error": str(e)}
