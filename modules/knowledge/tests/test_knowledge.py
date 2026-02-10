"""Tests for the Knowledge module."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from modules.knowledge import KnowledgeModule
from modules.knowledge.indexer import RepositoryIndexer


class TestRepositoryIndexer:
    @pytest.fixture
    def mock_memory(self):
        return MagicMock()

    def test_should_index(self, mock_memory):
        indexer = RepositoryIndexer({"extensions": [".py"]}, memory_module=mock_memory)
        
        with patch.object(Path, "is_file", return_value=True):
            assert indexer._should_index(Path("test.py")) is True
            assert indexer._should_index(Path("test.txt")) is False
            assert indexer._should_index(Path(".git/config")) is False

    def test_chunk_text(self, mock_memory):
        indexer = RepositoryIndexer({"chunk_size": 10}, memory_module=mock_memory)
        text = "1234567890abcde"
        chunks = indexer._chunk_text(text)
        assert len(chunks) == 2
        assert chunks[0] == "1234567890"
        assert chunks[1] == "abcde"

    def test_index_file(self, tmp_path, mock_memory):
        indexer = RepositoryIndexer({}, memory_module=mock_memory)
        
        test_file = tmp_path / "hello.py"
        test_file.write_text("print('hello')")
        
        indexer._index_file(test_file, tmp_path)
        
        assert mock_memory.remember.called
        args, kwargs = mock_memory.remember.call_args
        assert "hello.py" in args[0]
        assert args[1]["path"] == "hello.py"


class TestKnowledgeModule:
    def test_search(self):
        mock_memory = MagicMock()
        mock_memory.search.return_value = [{"text": "result"}]
        
        module = KnowledgeModule({"indexer": {}}, memory_module=mock_memory)
        results = module.search("query")
        
        assert results == [{"text": "result"}]
        mock_memory.search.assert_called_with("query", limit=5)
