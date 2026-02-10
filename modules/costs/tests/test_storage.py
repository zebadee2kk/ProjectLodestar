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

    def test_cleanup_all_with_zero_retention(self, storage, sample_record):
        storage.insert(sample_record)
        storage.insert(sample_record)
        # Backdate all records to 1 day ago — 0-day retention should remove them
        old_ts = (datetime.now() - timedelta(days=1)).isoformat()
        storage._conn.execute("UPDATE cost_records SET timestamp = ?", (old_ts,))
        storage._conn.commit()
        deleted = storage.cleanup(retention_days=0)
        assert deleted == 2
        assert storage.record_count() == 0

    def test_not_connected_raises(self, tmp_path):
        s = CostStorage(str(tmp_path / "nc.db"))
        with pytest.raises(RuntimeError, match="not connected"):
            s.cleanup()


class TestStorageEdgeCases:

    def test_close_sets_connection_none(self, tmp_path):
        s = CostStorage(str(tmp_path / "close_test.db"))
        s.connect()
        assert s._conn is not None
        s.close()
        assert s._conn is None

    def test_close_idempotent(self, tmp_path):
        s = CostStorage(str(tmp_path / "close_test.db"))
        s.connect()
        s.close()
        s.close()  # Should not raise
        assert s._conn is None

    def test_reconnect_after_close(self, tmp_path):
        db_path = str(tmp_path / "reconnect.db")
        s = CostStorage(db_path)
        s.connect()
        s.insert({"model": "x", "tokens_in": 100, "tokens_out": 50,
                  "cost": 0.01, "baseline_cost": 0.02, "savings": 0.01, "task": "test"})
        s.close()
        s.connect()
        # Data persists across reconnect
        assert s.record_count() == 1
        s.close()

    def test_insert_empty_task(self, storage):
        record = {
            "model": "gpt-3.5-turbo", "tokens_in": 100, "tokens_out": 50,
            "cost": 0.0, "baseline_cost": 0.01, "savings": 0.01, "task": "",
        }
        storage.insert(record)
        records = storage.query_all()
        assert records[0]["task"] == ""

    def test_insert_no_task_key(self, storage):
        record = {
            "model": "gpt-3.5-turbo", "tokens_in": 100, "tokens_out": 50,
            "cost": 0.0, "baseline_cost": 0.01, "savings": 0.01,
        }
        storage.insert(record)
        records = storage.query_all()
        assert records[0]["task"] == ""

    def test_large_token_counts(self, storage):
        record = {
            "model": "gpt-4o", "tokens_in": 1_000_000, "tokens_out": 500_000,
            "cost": 500.0, "baseline_cost": 600.0, "savings": 100.0, "task": "big",
        }
        storage.insert(record)
        records = storage.query_all()
        assert records[0]["tokens_in"] == 1_000_000
        assert records[0]["cost_usd"] == 500.0

    def test_query_all_ordering(self, storage, sample_record):
        """Records should be returned newest-first."""
        storage.insert({**sample_record, "task": "first"})
        storage.insert({**sample_record, "task": "second"})
        records = storage.query_all()
        # Last inserted should be first in results (DESC order)
        assert records[0]["task"] == "second"

    def test_total_cost_with_mixed_models(self, multi_model_storage):
        total = multi_model_storage.total_cost()
        # 0.0 + 0.0105 + 0.021 + 0.005 = 0.0365
        assert total == pytest.approx(0.0365, abs=0.0001)

    def test_db_directory_created(self, tmp_path):
        deep_path = str(tmp_path / "a" / "b" / "c" / "costs.db")
        s = CostStorage(deep_path)
        s.connect()
        s.close()
        # Directory should exist now
        assert (tmp_path / "a" / "b" / "c").exists()
