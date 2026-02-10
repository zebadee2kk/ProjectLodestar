"""Tests for the Memory module."""

import pytest
from unittest.mock import MagicMock, patch
from modules.memory import MemoryModule
from modules.memory.embeddings import EmbeddingManager
from modules.memory.store import VectorStore


class TestEmbeddingManager:
    @patch("litellm.embedding")
    def test_embed(self, mock_embedding):
        mock_embedding.return_value = MagicMock(data=[{"embedding": [0.1, 0.2, 0.3]}])
        manager = EmbeddingManager({"dimensions": 3})
        vector = manager.embed("hello")
        assert vector == [0.1, 0.2, 0.3]
        mock_embedding.assert_called_once()

    @patch("litellm.embedding")
    def test_embed_fallback(self, mock_embedding):
        mock_embedding.side_effect = Exception("error")
        manager = EmbeddingManager({"dimensions": 3})
        vector = manager.embed("hello")
        assert vector == [0.0, 0.0, 0.0]


class TestVectorStore:
    @patch("qdrant_client.QdrantClient")
    def test_upsert(self, mock_qdrant):
        mock_client = mock_qdrant.return_value
        mock_client.get_collections.return_value = MagicMock(collections=[])
        
        store = VectorStore({"url": None, "collection": "test"})
        store.connect()
        
        point_id = store.upsert([0.1, 0.2, 0.3], "content", {"meta": "data"})
        assert isinstance(point_id, str)
        mock_client.upsert.assert_called_once()

    @patch("qdrant_client.QdrantClient")
    def test_search(self, mock_qdrant):
        mock_client = mock_qdrant.return_value
        mock_client.get_collections.return_value = MagicMock(collections=[])
        
        mock_result = MagicMock()
        mock_result.id = "123"
        mock_result.score = 0.95
        mock_result.payload = {"text": "found it", "other": "data"}
        mock_client.search.return_value = [mock_result]
        
        store = VectorStore({"url": None, "collection": "test"})
        results = store.search([0.1, 0.2, 0.3])
        
        assert len(results) == 1
        assert results[0]["text"] == "found it"
        assert results[0]["metadata"]["other"] == "data"


class TestMemoryModule:
    @patch("modules.memory.embeddings.EmbeddingManager.embed")
    @patch("modules.memory.store.VectorStore.upsert")
    def test_remember(self, mock_upsert, mock_embed):
        mock_embed.return_value = [0.1, 0.2]
        mock_upsert.return_value = "id1"
        
        module = MemoryModule({"enabled": True})
        res = module.remember("some text")
        
        assert res == "id1"
        mock_embed.assert_called_with("some text")
        mock_upsert.assert_called_with([0.1, 0.2], "some text", None)
