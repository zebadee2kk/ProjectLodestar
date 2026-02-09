"""SQLite persistence for cost tracking data.

Provides durable storage and querying for cost records. The tracker
uses this to persist data across sessions.
"""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS cost_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    model TEXT NOT NULL,
    tokens_in INTEGER NOT NULL,
    tokens_out INTEGER NOT NULL,
    cost_usd REAL NOT NULL,
    baseline_cost_usd REAL NOT NULL,
    savings_usd REAL NOT NULL,
    task TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_cost_timestamp ON cost_records(timestamp);
CREATE INDEX IF NOT EXISTS idx_cost_model ON cost_records(model);
"""


class CostStorage:
    """SQLite storage backend for cost records.

    Args:
        db_path: Path to the SQLite database file.
    """

    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        """Open database connection and create schema if needed."""
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)

    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def insert(self, record: Dict[str, Any]) -> None:
        """Insert a single cost record.

        Args:
            record: Dict with model, tokens_in, tokens_out, cost,
                    baseline_cost, savings, task keys.
        """
        if not self._conn:
            raise RuntimeError("Database not connected. Call connect() first.")
        self._conn.execute(
            """INSERT INTO cost_records
               (model, tokens_in, tokens_out, cost_usd, baseline_cost_usd,
                savings_usd, task)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                record["model"],
                record["tokens_in"],
                record["tokens_out"],
                record["cost"],
                record["baseline_cost"],
                record["savings"],
                record.get("task", ""),
            ),
        )
        self._conn.commit()

    def query_all(self) -> List[Dict[str, Any]]:
        """Retrieve all cost records.

        Returns:
            List of record dicts.
        """
        if not self._conn:
            raise RuntimeError("Database not connected. Call connect() first.")
        cursor = self._conn.execute(
            "SELECT * FROM cost_records ORDER BY timestamp DESC"
        )
        return [dict(row) for row in cursor.fetchall()]

    def total_cost(self) -> float:
        """Get total cost from the database.

        Returns:
            Total cost in USD.
        """
        if not self._conn:
            raise RuntimeError("Database not connected. Call connect() first.")
        cursor = self._conn.execute(
            "SELECT COALESCE(SUM(cost_usd), 0) FROM cost_records"
        )
        return cursor.fetchone()[0]

    def total_savings(self) -> float:
        """Get total savings from the database.

        Returns:
            Total savings in USD.
        """
        if not self._conn:
            raise RuntimeError("Database not connected. Call connect() first.")
        cursor = self._conn.execute(
            "SELECT COALESCE(SUM(savings_usd), 0) FROM cost_records"
        )
        return cursor.fetchone()[0]
