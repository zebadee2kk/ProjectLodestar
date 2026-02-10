"""Repository indexing for Project Lodestar.

Handles walking the filesystem, chunking content, and generating embeddings.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

from modules.memory import MemoryModule

logger = logging.getLogger(__name__)


class RepositoryIndexer:
    """Indexes a repository by chunking files and storing embeddings.

    Args:
        config: Indexer configuration (excludes, chunk size, etc.).
    """

    def __init__(self, config: Dict[str, Any], memory_module: Optional[MemoryModule] = None) -> None:
        self.config = config
        self.excludes = config.get("excludes", [".git", "__pycache__", ".lodestar", "node_modules", ".pytest_cache"])
        self.chunk_size = config.get("chunk_size", 1000)
        self.supported_extensions = config.get("extensions", [".py", ".md", ".yaml", ".yml", ".json", ".txt"])
        
        # We need a memory module to store the embeddings.
        # It's passed in from the KnowledgeModule which manages its lifecycle.
        self.memory = memory_module

    def index_all(self, root_path: str) -> Dict[str, Any]:
        """Walk the repository and index all supported files."""
        root = Path(root_path)
        indexed_count = 0
        error_count = 0
        
        self.memory.start()
        
        for p in root.rglob("*"):
            if self._should_index(p):
                try:
                    self._index_file(p, root)
                    indexed_count += 1
                except Exception as e:
                    logger.error(f"Failed to index {p}: {e}")
                    error_count += 1
        
        return {
            "status": "completed",
            "indexed_files": indexed_count,
            "errors": error_count
        }

    def _should_index(self, path: Path) -> bool:
        """Check if a file should be indexed."""
        if not path.is_file():
            return False
            
        # Check excludes
        for exclude in self.excludes:
            if exclude in str(path):
                return False
                
        # Check extensions
        if path.suffix not in self.supported_extensions:
            return False
            
        return True

    def _index_file(self, path: Path, root: Path) -> None:
        """Index a single file."""
        relative_path = str(path.relative_to(root))
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            
        # Chunking strategy (simple for now: by line count or characters)
        chunks = self._chunk_text(content)
        
        for i, chunk in enumerate(chunks):
            metadata = {
                "path": relative_path,
                "chunk_index": i,
                "type": "code" if path.suffix != ".md" else "doc",
                "source": "knowledge_base"
            }
            # Prefix chunk with path for better context retrieval
            text_to_embed = f"File: {relative_path}\n\n{chunk}"
            self.memory.remember(text_to_embed, metadata)

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks of roughly chunk_size."""
        if len(text) <= self.chunk_size:
            return [text]
            
        chunks = []
        for i in range(0, len(text), self.chunk_size):
            chunks.append(text[i:i + self.chunk_size])
        return chunks

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search across the indexed repository knowledge."""
        self.memory.start()
        return self.memory.search(query, limit=limit)
