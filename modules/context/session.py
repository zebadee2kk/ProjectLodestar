"""Session management for Project Lodestar.

Handles persistent storage of AI work sessions and their history.
"""

import sqlite3
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
import logging
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages persistent sessions using SQLite.

    Args:
        config: Configuration for session persistence.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.db_path = Path(config.get("db_path", ".lodestar/sessions.db"))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    metadata TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    role TEXT,
                    content TEXT,
                    timestamp TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (id)
                )
            """)
            conn.commit()

    def create_session(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new session record."""
        session_id = str(uuid.uuid4())
        now = datetime.now()
        meta_json = json.dumps(metadata or {})
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO sessions (id, name, created_at, updated_at, metadata) VALUES (?, ?, ?, ?, ?)",
                (session_id, name, now, now, meta_json)
            )
            conn.commit()
        
        logger.info(f"Created session {session_id} ({name})")
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session record."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id, name, created_at, updated_at, metadata FROM sessions WHERE id = ?",
                (session_id,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "name": row[1],
                    "created_at": row[2],
                    "updated_at": row[3],
                    "metadata": json.loads(row[4])
                }
        return None

    def append_history(self, session_id: str, role: str, content: str) -> None:
        """Add a message to history and update session timestamp."""
        now = datetime.now()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO history (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (session_id, role, content, now)
            )
            conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (now, session_id)
            )
            conn.commit()

    def get_history(self, session_id: str, limit: int = 20) -> List[Dict[str, str]]:
        """Retrieve history for a session."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT role, content FROM history WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
                (session_id, limit)
            )
            rows = cursor.fetchall()
            # Return in chronological order
            return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT id, name, updated_at FROM sessions ORDER BY updated_at DESC")
            return [
                {"id": r[0], "name": r[1], "updated_at": r[2]}
                for r in cursor.fetchall()
            ]
