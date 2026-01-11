# WO-P2.2: AST Cache File Locks Implementation Plan

**Date**: 2026-01-06  
**Status**: ACTIVE  
**Priority**: P0 (Blocks global enable)

---

## Objective

Prevent SQLite corruption from concurrent CLI/daemon access by implementing advisory file locks with fail-closed strategy.

---

## Design Decision: Advisory Locks

**Why not SQLite WAL mode only?**
- WAL helps but doesn't prevent all corruption scenarios
- File lock is explicit, testable, and cross-platform

**Library**: `filelock` (cross-platform, simple API)
```bash
uv add filelock
```

**Lock Strategy**:
- Lock file: `{db_path}.lock`
- Acquire lock BEFORE any DB operation (get/set/delete/clear)
- Timeout: 5 seconds (configurable)
- **Fail-closed**: If lock unavailable → raise error + emit telemetry

---

## Implementation Tasks

### Task 1: Add filelock dependency

```bash
cd /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope
uv add filelock
```

---

### Task 2: Modify SQLiteCache with Lock

**File**: `src/domain/ast_cache.py`

**Changes**:
```python
from filelock import FileLock, Timeout as LockTimeout

class SQLiteCache:
    def __init__(self, db_path: Path, max_entries: int = 10000, max_bytes: int = 100 * 1024 * 1024, lock_timeout: float = 5.0):
        self.db_path = db_path
        self.lock_path = db_path.with_suffix('.lock')
        self.lock_timeout = lock_timeout
        # ...
        
    def _with_lock(self, operation: str, func):
        """Execute function with file lock acquired."""
        try:
            with FileLock(str(self.lock_path), timeout=self.lock_timeout):
                return func()
        except LockTimeout:
            # Emit telemetry if available
            raise RuntimeError(
                f"Could not acquire lock for {operation} after {self.lock_timeout}s. "
                f"Another process may be using the cache."
            )
    
    def get(self, key: str) -> Optional[Any]:
        """Get with lock."""
        def _get():
            # existing get logic
            ...
        return self._with_lock("get", _get)
```

**Note**: Reads might not need lock (SQLite readers don't block), but for simplicity and safety, lock all operations.

---

### Task 3: Telemetry for Lock Contention

**Problem**: TelemetryAstCache wraps SQLiteCache, but SQLiteCache doesn't have telemetry.

**Solution**: Pass telemetry to SQLiteCache constructor (optional).

**Changes**:
```python
class SQLiteCache:
    def __init__(
        self, 
        db_path: Path, 
        telemetry: Optional["Telemetry"] = None,  # NEW
        ...
    ):
        self.telemetry = telemetry
        
    def _with_lock(self, operation: str, func):
        try:
            with FileLock(...):
                return func()
        except LockTimeout as e:
            if self.telemetry:
                self.telemetry.event(
                    cmd="ast.cache.lock_timeout",
                    args={"operation": operation, "timeout_sec": self.lock_timeout},
                    result={"db_path": str(self.lock_path)},
                    timing_ms=int(self.lock_timeout * 1000)
                )
            raise RuntimeError(...) from e
```

**Update Factory**:
```python
def get_ast_cache(..., telemetry: ...):
    if should_persist:
        cache = SQLiteCache(db_path=db_path, telemetry=telemetry, ...)
    else:
        cache = InMemoryLRUCache(...)
    
    # Wrap with telemetry (but SQLiteCache already has it for lock events)
    if telemetry is not None:
        return TelemetryAstCache(cache, telemetry, segment_id)
    return cache
```

---

### Task 4: E2E Concurrency Test

**File**: `tests/integration/test_ast_cache_concurrency.py`

**Test Case 1**: Concurrent writes don't corrupt
```python
import multiprocessing
import time

def worker(db_path, worker_id, iterations):
    """Worker that writes to cache repeatedly."""
    cache = SQLiteCache(db_path)
    for i in range(iterations):
        key = f"worker_{worker_id}_key_{i}"
        cache.set(key, {"data": f"value_{i}"})
        time.sleep(0.01)  # Small delay to increase contention

def test_concurrent_writes_no_corruption(tmp_path):
    """Verify concurrent writes don't corrupt SQLite DB."""
    db_path = tmp_path / "test.db"
    
    # Spawn 2 workers
    workers = [
        multiprocessing.Process(target=worker, args=(db_path, 0, 10)),
        multiprocessing.Process(target=worker, args=(db_path, 1, 10)),
    ]
    
    for w in workers:
        w.start()
    for w in workers:
        w.join()
    
    # Verify DB is not corrupted
    cache = SQLiteCache(db_path)
    stats = cache.stats()
    assert stats.entries == 20  # 10 from each worker
```

**Test Case 2**: Lock timeout behavior
```python
def test_lock_timeout_raises_error(tmp_path):
    """Verify lock timeout raises clear error."""
    db_path = tmp_path / "test.db"
    
    # Hold lock manually
    lock_path = db_path.with_suffix('.lock')
    lock = FileLock(str(lock_path), timeout=0.1)
    lock.acquire()
    
    try:
        # Try to use cache (should timeout)
        cache = SQLiteCache(db_path, lock_timeout=0.5)
        with pytest.raises(RuntimeError, match="Could not acquire lock"):
            cache.set("key", "value")
    finally:
        lock.release()
```

---

## Alternative: Read-Write Lock Optimization

**Current**: Lock ALL operations (get/set/delete/clear)  
**Optimization**: Use shared lock for reads, exclusive for writes

**Trade-off**:
- **Pro**: Better performance (multiple readers OK)
- **Con**: More complexity, SQLite already handles reader concurrency

**Decision**: Start with simple (lock all), optimize later if needed.

---

## Acceptance Criteria (DoD)

- [ ] `filelock` dependency added
- [ ] `SQLiteCache._with_lock()` implemented
- [ ] All operations (get/set/delete/clear) use lock
- [ ] Lock timeout emits telemetry event
- [ ] E2E concurrency test (2 workers, no corruption)
- [ ] Regression: All P1/P2.1 tests pass

---

## Performance Impact

**Overhead**: ~1-2ms per operation (lock acquire/release)  
**Acceptable**: Yes, correctness > speed  
**Future**: Profile and optimize if needed

---

## Security Note

**Lock file location**: Same directory as DB  
**Permissions**: Inherited from DB directory  
**Cleanup**: filelock auto-cleans stale locks
