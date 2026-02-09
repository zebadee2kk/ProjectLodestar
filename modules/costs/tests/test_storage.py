"""Tests for the CostStorage SQLite backend."""

import pytest
from modules.costs.storage import CostStorage


@pytest.fixture
def storage(tmp_path):
    """A CostStorage connected to a temp database."""
    db_path = str(tmp_path / "test_costs.db")
    s = CostStorage(db_path)
    s.connect()
    yield s
    s.close()


@pytest.fixture
def sample_record():
    return {
        "model": "gpt-3.5-turbo",
        "tokens_in": 1000,
        "tokens_out": 500,
        "cost": 0.0,
        "baseline_cost": 0.0105,
        "savings": 0.0105,
        "task": "bug_fix",
    }


class TestCostStorage:

    def test_connect_creates_tables(self, storage):
        rows = storage._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [r[0] for r in rows]
        assert "cost_records" in table_names

    def test_insert_and_query(self, storage, sample_record):
        storage.insert(sample_record)
        records = storage.query_all()
        assert len(records) == 1
        assert records[0]["model"] == "gpt-3.5-turbo"
        assert records[0]["tokens_in"] == 1000

    def test_total_cost(self, storage, sample_record):
        storage.insert(sample_record)
        assert storage.total_cost() == 0.0

    def test_total_savings(self, storage, sample_record):
        storage.insert(sample_record)
        assert storage.total_savings() == 0.0105

    def test_empty_totals(self, storage):
        assert storage.total_cost() == 0.0
        assert storage.total_savings() == 0.0

    def test_not_connected_raises(self, tmp_path):
        s = CostStorage(str(tmp_path / "not_connected.db"))
        with pytest.raises(RuntimeError, match="not connected"):
            s.insert({"model": "x", "tokens_in": 0, "tokens_out": 0,
                       "cost": 0, "baseline_cost": 0, "savings": 0})

    def test_multiple_inserts(self, storage, sample_record):
        for _ in range(5):
            storage.insert(sample_record)
        records = storage.query_all()
        assert len(records) == 5
