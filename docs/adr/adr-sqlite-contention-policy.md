# ADR: SQLite Contention Policy

## Status
ACCEPTED

## Context
The RepoStore uses SQLite for metadata storage. We need to define how concurrent writes are handled.

## Decision
We use SQLite's default contention handling: **Option B - Internal Serialization**

### Behavior
- SQLite uses file-level locking to serialize concurrent writes
- Multiple writers are automatically queued and processed sequentially
- No explicit error is raised for contention
- The final state is always consistent

### Evidence
- Test: `tests/integration/test_sqlite_contention.py::test_concurrent_writers_no_corruption`
  - 10 concurrent writers complete successfully
  - All repos are stored without corruption
  - No duplicate repo_ids

- Test: `tests/integration/test_sqlite_contention.py::test_database_integrity_after_contention`
  - 20 concurrent writes complete
  - DB passes integrity check (`PRAGMA integrity_check`)
  - All records are consistent

### Performance Characteristics
- SQLite's default busy timeout (5 seconds) handles transient contention
- No WAL mode required for current workload (characterized, not over-engineered)
- On-disk DB uses kernel-level file locking (not mockable in `:memory:`)

## Alternatives Considered

### Option A: Explicit Error on Contention
- **Pros**: Fail-fast, explicit error handling
- **Cons**: Requires retry logic in callers, more complex
- **Rejected**: Over-engineering for current workload

### WAL Mode
- **Pros**: Better concurrent read performance
- **Cons**: Additional complexity, not needed for current workload
- **Rejected**: Characterization shows default mode is sufficient

## Consequences

### Positive
- Simple implementation (no custom locking)
- SQLite handles contention transparently
- Consistent final state guaranteed by SQLite

### Negative
- Contention is absorbed silently (no telemetry on wait times)
- High contention scenarios may experience latency

### Mitigation
- Monitor write latency in production
- If contention becomes an issue, add telemetry or consider WAL mode

## References
- Plan: `.sisyphus/plans/e-v1-runtime-maturity-plan.md` (WO-M4)
- Tests: `tests/integration/test_sqlite_contention.py`
- SQLite Docs: https://www.sqlite.org/lockingv3.html
