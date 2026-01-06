# Implementation Plan: WO-P3.0 AST Cache Soak Run

## Goal
Verify operational readiness of AST Cache Persistence (`SQLiteCache`) through a rigorous "Soak Run" simulating realistic high-load usage, validating telemetry, concurrency, and data integrity.

## Prerequisites
- WO-P2.2 (File Locks) complete & verified.
- `TRIFECTA_AST_PERSIST=1` support enabled.

## Strategy
Execute `scripts/run_soak.sh`, a bash harness that:
1. Enables persistence.
2. Runs concurrent generic queries + symbol extractions (200+ operations).
3. Injects interference (locks via `flock`).
4. Verifies post-run database integrity.
5. Extracts "Real" telemetry samples.

## Deliverables

### 1. Soak Harness (`scripts/run_soak.sh`)
Bash script orchestrating:
- Clean start (fresh persistence DB).
- Parallel execution of `trifecta ast symbols` and `trifecta ctx search`.
- Monitoring of cache file growth.
- Final integrity check via `sqlite3`.

### 2. Soak Test Suite (`tests/soak/test_ast_cache_soak.py`)
Python integration test driving the soak logic (reusable, verified by pytest).
- Validates 200+ writes/hits.
- Asserts P95 latency < 10ms.
- Asserts lock_wait events present.

### 3. Audit Report (`docs/reports/ast_soak_run.md`)
Evidence of:
- Cache hit rate improvement (cold vs warm).
- Lock contention handling (telemetry events).
- Zero corruption (integrity_check=ok).

## Tasks

### Phase 1: Harness & Test
- [ ] Create `tests/soak/test_ast_cache_soak.py` (heavy load logic).
- [ ] Create `scripts/run_soak.sh` (orchestration wrapper).

### Phase 2: Execution (Soak)
- [ ] Run `bash scripts/run_soak.sh` (duration ~5 min).
- [ ] Tail `_ctx/telemetry/events.jsonl` for anomalies.

### Phase 3: Analysis & Report
- [ ] Extract `ast.cache.lock_wait` events using `jq`.
- [ ] Calculate latency stats.
- [ ] Generated `docs/reports/ast_soak_run.md`.

## Verification
- `bash scripts/run_soak.sh` exit code 0.
- Telemetry shows `lock_wait` > 0 if contention occurred.
- `sqlite3 .trifecta/cache/ast_cache_*.db "PRAGMA integrity_check"` returns "ok".
