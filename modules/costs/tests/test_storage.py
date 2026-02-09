"""Tests for the CostStorage SQLite backend."""

import pytest
from datetime import datetime, timedelta
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


@pytest.fixture
def multi_model_storage(storage, sample_record):
    """Storage with records from multiple models."""
    storage.insert(sample_record)
    storage.insert({**sample_record, "model": "claude-sonnet", "cost": 0.0105, "savings": 0.0})
    storage.insert({**sample_record, "model": "claude-sonnet", "cost": 0.021, "savings": 0.0})
    storage.insert({**sample_record, "model": "gpt-4o", "cost": 0.005, "savings": 0.0055})
    return storage


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


class TestQueryByModel:

    def test_filter_single_model(self, multi_model_storage):
        records = multi_model_storage.query_by_model("claude-sonnet")
        assert len(records) == 2
        assert all(r["model"] == "claude-sonnet" for r in records)

    def test_filter_returns_empty(self, multi_model_storage):
        records = multi_model_storage.query_by_model("nonexistent-model")
        assert records == []

    def test_filter_free_model(self, multi_model_storage):
        records = multi_model_storage.query_by_model("gpt-3.5-turbo")
        assert len(records) == 1

    def test_not_connected_raises(self, tmp_path):
        s = CostStorage(str(tmp_path / "nc.db"))
        with pytest.raises(RuntimeError, match="not connected"):
            s.query_by_model("x")


class TestQueryByDateRange:

    def test_range_captures_recent(self, storage, sample_record):
        storage.insert(sample_record)
        start = datetime.now() - timedelta(hours=1)
        end = datetime.now() + timedelta(hours=1)
        records = storage.query_by_date_range(start, end)
        assert len(records) == 1

    def test_range_misses_future(self, storage, sample_record):
        storage.insert(sample_record)
        start = datetime.now() + timedelta(days=1)
        end = datetime.now() + timedelta(days=2)
        records = storage.query_by_date_range(start, end)
        assert records == []

    def test_not_connected_raises(self, tmp_path):
        s = CostStorage(str(tmp_path / "nc.db"))
        with pytest.raises(RuntimeError, match="not connected"):
            s.query_by_date_range(datetime.now(), datetime.now())


class TestRecordCount:

    def test_empty_count(self, storage):
        assert storage.record_count() == 0

    def test_count_after_inserts(self, multi_model_storage):
        assert multi_model_storage.record_count() == 4

    def test_not_connected_raises(self, tmp_path):
        s = CostStorage(str(tmp_path / "nc.db"))
        with pytest.raises(RuntimeError, match="not connected"):
            s.record_count()


class TestCleanup:

    def test_cleanup_keeps_recent(self, storage, sample_record):
        storage.insert(sample_record)
        deleted = storage.cleanup(retention_days=90)
        assert deleted == 0
        assert storage.record_count() == 1

    def test_cleanup_removes_old(self, storage, sample_record):
        storage.insert(sample_record)
        # Manually backdate the record to 100 days ago
        old_ts = (datetime.now() - timedelta(days=100)).isoformat()
        storage._conn.execute(
            "UPDATE cost_records SET timestamp = ?", (old_ts,)
        )
        storage._conn.commit()
        deleted = storage.cleanup(retention_days=90)
        assert deleted == 1
        assert storage.record_count() == 0

    def test_cleanup_partial(self, storage, sample_record):
        # Insert two records, backdate only one
        storage.insert(sample_record)
        storage.insert(sample_record)
        old_ts = (datetime.now() - timedelta(days=100)).isoformat()
        storage._conn.execute(
            "UPDATE cost_records SET timestamp = ? WHERE id = 1", (old_ts,)
        )
        storage._conn.commit()
        deleted = storage.cleanup(retention_days=90)
        assert deleted == 1
        assert storage.record_count() == 1

    def test_not_connected_raises(self, tmp_path):
        s = CostStorage(str(tmp_path / "nc.db"))
        with pytest.raises(RuntimeError, match="not connected"):
            s.cleanup()
