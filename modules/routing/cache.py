"""Response caching for LLM requests."""

import hashlib
import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS response_cache (
    key TEXT PRIMARY KEY,
    response_json TEXT NOT NULL,
    created_at REAL NOT NULL,
    last_accessed REAL NOT NULL,
    model TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cache_accessed ON response_cache(last_accessed);
"""

class CacheManager:
    """Manages a file-based cache for LLM responses."""

    def __init__(self, db_path: str = ".lodestar/cache.db", ttl_seconds: int = 86400) -> None:
        self.db_path = Path(db_path)
        self.ttl_seconds = ttl_seconds
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        """Open database connection."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def get(self, model: str, messages: list, **kwargs) -> Optional[Dict[str, Any]]:
        """Retrieve a cached response if valid."""
        if not self._conn:
            self.connect()

        key = self._generate_key(model, messages, kwargs)
        
        cursor = self._conn.execute(
            "SELECT response_json, created_at FROM response_cache WHERE key = ?",
            (key,)
        )
        row = cursor.fetchone()
        
        if row:
            # Check TTL
            if time.time() - row["created_at"] > self.ttl_seconds:
                self._delete(key)
                return None
            
            # Update last accessed
            self._conn.execute(
                "UPDATE response_cache SET last_accessed = ? WHERE key = ?",
                (time.time(), key)
            )
            self._conn.commit()
            
            logger.info(f"Cache HIT for key {key[:8]}")
            return json.loads(row["response_json"])
            
        return None

    def set(self, model: str, messages: list, response: Dict[str, Any], **kwargs) -> None:
        """Cache a response."""
        if not self._conn:
            self.connect()
            
        key = self._generate_key(model, messages, kwargs)
        
        self._conn.execute(
            """INSERT OR REPLACE INTO response_cache 
               (key, response_json, created_at, last_accessed, model) 
               VALUES (?, ?, ?, ?, ?)""",
            (
                key,
                json.dumps(response),
                time.time(),
                time.time(),
                model
            )
        )
        self._conn.commit()

    def clear(self) -> int:
        """Clear all cache entries."""
        if not self._conn:
            self.connect()
        cursor = self._conn.execute("DELETE FROM response_cache")
        self._conn.commit()
        return cursor.rowcount

    def stats(self) -> Dict[str, Any]:
        """Return cache statistics."""
        if not self._conn:
            self.connect()
            
        cursor = self._conn.execute("SELECT COUNT(*), SUM(LENGTH(response_json)) FROM response_cache")
        count, size = cursor.fetchone()
        return {
            "entries": count or 0,
            "size_bytes": size or 0,
            "db_path": str(self.db_path)
        }

    def _generate_key(self, model: str, messages: list, kwargs: Dict[str, Any]) -> str:
        """Generate a stable hash key for the request."""
        # Sort kwargs to ensure stability
        stable_kwargs = json.dumps(kwargs, sort_keys=True)
        stable_messages = json.dumps(messages, sort_keys=True)
        content = f"{model}|{stable_messages}|{stable_kwargs}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _delete(self, key: str) -> None:
        """Delete a specific key."""
        self._conn.execute("DELETE FROM response_cache WHERE key = ?", (key,))
        self._conn.commit()
