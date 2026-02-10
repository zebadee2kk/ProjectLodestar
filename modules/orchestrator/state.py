"""Orchestration run state persistence (SQLite-backed).

Stores a lightweight record of each orchestration run so the CLI can
report history and the user can resume failed runs in the future.
"""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

_DEFAULT_DB = Path.home() / ".lodestar" / "orchestrator_runs.db"

_CREATE_RUNS = """
CREATE TABLE IF NOT EXISTS orchestration_runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      TEXT    NOT NULL UNIQUE,
    playbook    TEXT,
    request     TEXT    NOT NULL,
    status      TEXT    NOT NULL DEFAULT 'running',
    total_cost  REAL    NOT NULL DEFAULT 0.0,
    step_count  INTEGER NOT NULL DEFAULT 0,
    artifacts   TEXT,
    summary     TEXT,
    started_at  REAL    NOT NULL,
    finished_at REAL
);
"""


@dataclass
class RunRecord:
    """Lightweight summary of a completed or in-progress run."""

    run_id: str
    playbook: Optional[str]
    request: str
    status: str
    total_cost: float
    step_count: int
    artifacts: Dict[str, Any]
    summary: str
    started_at: float
    finished_at: Optional[float] = None


class OrchestrationStateStore:
    """Persists orchestration run metadata to a local SQLite database.

    Args:
        db_path: Path to the SQLite database. Defaults to
                 ``~/.lodestar/orchestrator_runs.db``.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = Path(db_path) if db_path else _DEFAULT_DB
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_run(self, run_id: str, request: str, playbook: Optional[str] = None) -> None:
        """Insert a new run record with status 'running'."""
        with self._connect() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO orchestration_runs
                   (run_id, playbook, request, status, started_at)
                   VALUES (?, ?, ?, 'running', ?)""",
                (run_id, playbook, request, time.time()),
            )

    def complete_run(
        self,
        run_id: str,
        success: bool,
        total_cost: float,
        step_count: int,
        artifacts: Dict[str, Any],
        summary: str,
    ) -> None:
        """Mark a run as completed (or failed) with final metrics."""
        status = "completed" if success else "failed"
        with self._connect() as conn:
            conn.execute(
                """UPDATE orchestration_runs
                   SET status=?, total_cost=?, step_count=?,
                       artifacts=?, summary=?, finished_at=?
                   WHERE run_id=?""",
                (
                    status,
                    total_cost,
                    step_count,
                    json.dumps({k: str(v) for k, v in artifacts.items()}),
                    summary,
                    time.time(),
                    run_id,
                ),
            )

    def get_run(self, run_id: str) -> Optional[RunRecord]:
        """Fetch a single run by ID."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM orchestration_runs WHERE run_id=?", (run_id,)
            ).fetchone()
        return self._row_to_record(row) if row else None

    def list_runs(self, limit: int = 20) -> List[RunRecord]:
        """Return the most recent runs, newest first."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM orchestration_runs ORDER BY started_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._row_to_record(r) for r in rows]

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(_CREATE_RUNS)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.db_path))

    @staticmethod
    def _row_to_record(row: Any) -> RunRecord:
        artifacts_json = row[6] if len(row) > 6 else "{}"
        try:
            artifacts = json.loads(artifacts_json or "{}")
        except Exception:
            artifacts = {}
        return RunRecord(
            run_id=row[1],
            playbook=row[2],
            request=row[3],
            status=row[4],
            total_cost=row[5],
            step_count=int(row[6]) if isinstance(row[6], (int, float)) else 0,
            artifacts=artifacts if isinstance(artifacts, dict) else {},
            summary=row[8] or "" if len(row) > 8 else "",
            started_at=row[9] if len(row) > 9 else 0.0,
            finished_at=row[10] if len(row) > 10 else None,
        )
