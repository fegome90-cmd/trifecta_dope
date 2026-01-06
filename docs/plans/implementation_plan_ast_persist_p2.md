# AST Persistence P2 - Production Hardening Plan

**Date**: 2026-01-06  
**Status**: PLANNING  
**Depends On**: P1 (SHA `354afb6`) ✅ VERIFIED

---

## Context

P1 delivered **basic** persistence via factory + env var. Verification (Gates 1-3) confirmed:
- ✅ Cross-process cache hits work
- ✅ Single source of truth (factory)
- ✅ Deterministic paths

**However**, P1 is **not production-hardened**. P2 addresses observability, concurrency, and failure modes.

---

## P2 Goals

1. **Observability**: Know when cache helps/hurts
2. **Concurrency Safety**: CLI + daemon don't corrupt DB
3. **Failure Recovery**: Detect + recover from corruption
4. **Resource Management**: Control DB growth

---

## Task Breakdown

### Task 1: Telemetry Integration

**Objective**: Emit `cache_hit` and `cache_miss` events to `_ctx/telemetry/events.jsonl`.

**Implementation**:
1. Modify `src/domain/ast_cache.py`:
   - `SQLiteCache.get()`: Emit `cache.hit` or `cache.miss` event
   - `InMemoryLRUCache.get()`: Same
2. Wire telemetry instance to cache (DI):
   - Factory accepts optional `telemetry: Telemetry`
   - Pass from CLI/PR2 down to cache
3. Event schema:
   ```json
   {
     "cmd": "ast.cache.hit",
     "args": {"cache_key": "..."},
     "result": {"status": "hit"},
     "timing_ms": 2,
     "cache_type": "sqlite"
   }
   ```

**Acceptance**:
- `jq 'select(.cmd == "ast.cache.hit")' _ctx/telemetry/events.jsonl` shows hits
- E2E test verifies event appears on second run

---

### Task 2: File Locks (Multi-Process Safety)

**Objective**: Prevent CLI/daemon from corrupting shared SQLite DB.

**Implementation**:
1. Use `fcntl.flock()` (Unix) or equivalent:
   ```python
   import fcntl
   lock_file = db_path.with_suffix('.lock')
   with open(lock_file, 'w') as f:
       fcntl.flock(f.fileno(), fcntl.LOCK_EX)
       # SQLite operations
   ```
2. Add timeout (e.g., 5s). If lock unavailable → fallback to InMemory.
3. Emit `ast.cache.lock_timeout` telemetry event.

**Acceptance**:
- Concurrent test: Run 2 `trifecta ast symbols` simultaneously
- One gets lock, other falls back (no corruption)
- Telemetry shows `lock_timeout` event

---

### Task 3: Corruption Detection & Recovery

**Objective**: Detect corrupted DB and rebuild automatically.

**Implementation**:
1. **Checksum validation** (on load):
   ```python
   with sqlite3.connect(db_path) as conn:
       try:
           conn.execute("PRAGMA integrity_check").fetchone()
       except sqlite3.DatabaseError:
           # Corruption detected
           db_path.unlink()
           return InMemoryLRUCache()  # Fallback
   ```
2. Emit `ast.cache.corruption_detected` event.
3. Graceful degradation: Rebuild cache on next access.

**Acceptance**:
- Manually corrupt DB (`echo "garbage" >> ast_cache.db`)
- Verify system falls back + emits event
- Next run rebuilds successfully

---

### Task 4: Resource Monitoring

**Objective**: Alert when cache grows too large or entries expire.

**Implementation**:
1. **DB Size Check** (on init):
   ```python
   db_size_mb = db_path.stat().st_size / (1024 * 1024)
   if db_size_mb > 500:  # 500MB threshold
       emit_event("ast.cache.size_warning", {"size_mb": db_size_mb})
   ```
2. **Entry Count/Age**:
   - Query: `SELECT COUNT(*), MAX(last_access) FROM cache`
   - Emit stats periodically

**Acceptance**:
- Create large DB (e.g., 600MB)
- Verify warning event appears
- Dashboard (future) shows size trends

---

### Task 5: TTL & Eviction Policy

**Objective**: Auto-evict stale entries (e.g., files deleted/modified).

**Implementation**:
1. Add `file_mtime` column to cache table:
   ```sql
   ALTER TABLE cache ADD COLUMN file_mtime REAL;
   ```
2. On cache load:
   - Compare `file_mtime` in DB vs actual file
   - If mismatch → invalidate entry
3. Periodic cleanup (e.g., on daemon startup):
   - Delete entries > 7 days old

**Acceptance**:
- Modify source file
- Verify next run rebuilds (not cache hit)
- Old entries pruned after TTL

---

## Risk Assessment

| Task | Complexity | Blast Radius | Priority |
|------|-----------|--------------|----------|
| Telemetry | LOW | Low (additive) | P0 |
| File Locks | MEDIUM | High (concurrency) | P0 |
| Corruption | MEDIUM | Medium (fallback) | P1 |
| Monitoring | LOW | Low (logging) | P2 |
| TTL | HIGH | High (invalidation logic) | P2 |

---

## Recommended Execution Order

**Sprint 1 (Observability)**:
1. Task 1: Telemetry
2. Task 4: Monitoring

**Sprint 2 (Safety)**:
3. Task 2: File Locks
4. Task 3: Corruption Recovery

**Sprint 3 (Optimization)**:
5. Task 5: TTL (if needed based on telemetry)

---

## Dependencies

- **P1 Complete**: ✅ (SHA `354afb6`)
- **Telemetry System**: ✅ (`src/infrastructure/telemetry.py` exists)
- **SQLite Version**: Check WAL mode support (`PRAGMA journal_mode=WAL`)

---

## Success Metrics

**After P2**:
- [ ] 90%+ cache hit rate in CI (telemetry)
- [ ] Zero corruption incidents (30 days)
- [ ] Zero lock timeouts (typical workload)
- [ ] DB size < 100MB (for trifecta_dope repo)

---

## Exit Criteria (DoD)

- [ ] All 5 tasks have passing E2E tests
- [ ] Telemetry dashboard shows cache effectiveness
- [ ] Stress test: 10 concurrent CLI runs (no corruption)
- [ ] Walkthrough document with evidence

---

## Notes

**Why not use SQLite WAL mode?**
- Could reduce lock contention
- Research: `PRAGMA journal_mode=WAL` in `_init_db()`
- May replace Task 2 (file locks) if effective

**Alternative: Redis/Memcached?**
- Overkill for single-dev setup
- SQLite is good enough for <100 concurrent users

**Migration Path**:
- If P2 Task 5 (TTL) adds `file_mtime` column, need migration script
- Consider versioning: `PRAGMA user_version`
