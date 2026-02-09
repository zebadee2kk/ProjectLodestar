# ADR-0005: Cost Storage Architecture

**Status:** Accepted
**Date:** 2026-02-09
**Deciders:** Lodestar Team

## Context

The cost tracking module needs durable storage for request cost records
so that users can view historical trends, generate reports, and track
budgets across sessions. The storage layer must:

- Persist across process restarts
- Support efficient queries (by model, by date range, totals)
- Work on a single-user Debian VM with no external services
- Handle the expected volume (~100-3,000 requests/day)
- Support a configurable retention period (default 90 days)

## Decision

Use **SQLite** as the sole persistence backend for cost data.

### Schema

```sql
CREATE TABLE cost_records (
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

CREATE INDEX idx_cost_timestamp ON cost_records(timestamp);
CREATE INDEX idx_cost_model ON cost_records(model);
```

### Storage Location

Database file at `~/.lodestar/costs.db`. The directory is created
automatically if it doesn't exist.

### Retention

Records older than 90 days (configurable) will be purged by a
periodic cleanup job. No data is deleted automatically without
explicit configuration.

### Architecture

```
CostTracker (in-memory ledger)
    |
    +--> CostStorage (SQLite)
    |       - insert() per request
    |       - query_all(), total_cost(), total_savings()
    |
    +--> reporter (CLI output)
            - format_summary() for terminal display
```

The CostTracker maintains an in-memory ledger for the current session
and delegates persistence to CostStorage. This means queries within
a session are instant (no DB round-trip) while historical data is
available from SQLite.

## Consequences

### Positive
- Zero external dependencies (SQLite is in Python stdlib)
- Single file, easy to backup (`cp costs.db costs.db.bak`)
- Indexed queries fast enough for expected volume
- No server process to manage
- Works offline

### Negative
- Single-writer only (no concurrent multi-process writes)
- No built-in replication or high availability
- Schema migrations must be handled manually
- Not suitable if multi-user/multi-VM support is added later

### Neutral
- Can export to CSV/JSON for external analysis
- Can migrate to PostgreSQL later if needed (SQL is portable)
- 90-day retention keeps DB small (~1MB for 100k records)

## Alternatives Considered

1. **JSON file logging** — Append-only JSON lines. Simpler but no
   indexing, slow queries over large datasets, no atomic writes.

2. **PostgreSQL** — Full RDBMS. Overkill for single-user, requires
   running a server process, adds operational complexity.

3. **Redis** — Fast in-memory store. Data lost on restart unless
   configured for persistence, overkill for this use case.

4. **DuckDB** — Columnar analytics DB. Better for aggregation queries
   but less battle-tested, not in stdlib, heavier dependency.

## Implementation Notes

**Module:** `modules/costs/storage.py`
- `CostStorage` class with connect/close/insert/query_all/total_cost/total_savings
- Schema created automatically on first connect via `CREATE TABLE IF NOT EXISTS`
- Parameterized queries throughout (SQL injection safe)
- `tmp_path` fixtures in tests ensure no test pollution

**Future enhancements:**
- Add retention cleanup job (`DELETE WHERE timestamp < ?`)
- Add `query_by_model()` and `query_by_date_range()` methods
- Add CSV/JSON export from storage layer
- Add schema versioning if migrations become necessary
