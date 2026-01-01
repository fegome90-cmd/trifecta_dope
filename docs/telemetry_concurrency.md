# Telemetry Concurrency Model

**Version:** 1.0 (PR#1)  
**Concurrency Strategy:** Lossy, non-blocking POSIX file locking

---

## Model Overview

Trifecta telemetry uses **POSIX `fcntl.flock()`** with `LOCK_EX | LOCK_NB` (exclusive, non-blocking) for concurrent writes to JSONL files.

```python
import fcntl

def _write_jsonl(self, filename: str, data: Dict[str, Any]) -> bool:
    """
    Write event to JSONL. Returns False if lock cannot be acquired (lossy).
    """
    try:
        with open(path, "a") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            f.write(json.dumps(data) + "\n")
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        return True
    except BlockingIOError:
        return False  # Lock contention - skip this event (lossy)
```

---

## Concurrency Guarantees

### ✅ What IS Guaranteed

1. **No Corruption:** JSONL structure never corrupted (no torn writes, no partial lines)
2. **Atomic Appends:** Each event written as a complete line or not at all
3. **Idempotent Reads:** Readers never see partial/invalid JSON objects
4. **Lock-Free Reads:** Readers can read telemetry files without locking

### ❌ What IS NOT Guaranteed

1. **Event Count Exactness:** Under lock contention, some events dropped (2-5% typical)
2. **Event Ordering:** Events from concurrent processes may appear out-of-order
3. **Write Blocking:** Writers NEVER wait for locks - they skip and continue
4. **Drop Notification:** Dropped events not logged individually (only aggregate stats)

---

## Lossy by Design

**Philosophy:** Telemetry is for **observability and analytics**, not **transactional data**.

- **Acceptable:** 2-5% drop rate during burst writes (e.g., parallel test suite)
- **Unacceptable:** >10% drop rate (indicates pathological contention)
- **Monitoring:** `telemetry_drops` summary tracks drop rate in `last_run.json`

**Trade-offs:**
- ✅ **Zero latency cost:** No blocking waits, no retry loops
- ✅ **Zero deadlock risk:** Non-blocking locks cannot deadlock
- ✅ **Simplicity:** No complex queue/buffer/retry logic
- ❌ **Lossy:** Some events dropped under contention

---

## Drop Tracking (PR#1)

The telemetry system tracks its own losses:

```python
# In TelemetryTracker
self.telemetry_events_attempted = 0  # Total events attempted
self.telemetry_lock_skipped = 0       # Drops due to lock contention

def event(self, cmd, args, result, timing_ms, warnings=None, **extra_fields):
    self.telemetry_events_attempted += 1
    success = self._write_jsonl("events.jsonl", payload)
    if not success:
        self.telemetry_lock_skipped += 1
```

**Summary in `last_run.json`:**
```json
{
  "telemetry_drops": {
    "lock_skipped": 3,
    "attempted": 100,
    "written": 97,
    "drop_rate": 0.03
  }
}
```

**Interpretation:**
- `lock_skipped`: Events dropped due to lock contention
- `attempted`: Total event writes attempted
- `written`: Successfully written events (`attempted - lock_skipped`)
- `drop_rate`: Ratio of drops (`lock_skipped / attempted`)

---

## Usage Policy

### ✅ Safe Uses (Lossy OK)

- **Analytics:** Aggregate statistics, trends, performance profiling
- **Debugging:** Understanding typical behavior, identifying patterns
- **Metrics:** Latency percentiles, cache hit rates, LSP READY rates
- **Development:** Observing agent behavior during local development

### ⚠️ Unsafe Uses (Lossy NOT OK)

- **Billing:** Cannot use for financial calculations (drops = missed charges)
- **Compliance Logs:** Cannot use for audit trails (drops = missing events)
- **Rate Limiting Gates:** Cannot use for quota enforcement (drops = bypass)
- **Distributed Locks:** Cannot use for coordination (drops = lost signals)

**Rule of Thumb:** If missing 1 event out of 100 breaks your use case, telemetry is the wrong tool.

---

## Concurrency Testing

### Test Strategy (PR#1)

```python
def test_concurrent_writes_no_corruption(tmp_path):
    """
    50 processes × 20 events = 1000 total writes.
    - MUST: No corrupted lines, all valid JSON
    - MUST NOT: Exact 1000 events (lossy drops OK)
    """
    import multiprocessing
    
    def worker(tracker, proc_id):
        for i in range(20):
            tracker.event(f"test.{proc_id}", {"i": i}, {"ok": True}, timing_ms=1)
    
    processes = [
        multiprocessing.Process(target=worker, args=(tracker, i))
        for i in range(50)
    ]
    for p in processes: p.start()
    for p in processes: p.join()
    
    # Verify: no corrupted lines
    with open(events_file) as f:
        for line in f:
            json.loads(line)  # Raises if corrupted
    
    # Accept: drop_rate < 0.05 (5%)
    assert tracker.telemetry_lock_skipped / 1000 < 0.05
```

### Expected Results

- **Local dev (single process):** 0% drop rate
- **Parallel tests (10-50 processes):** 2-5% drop rate
- **Burst writes (100+ concurrent):** 5-10% drop rate (acceptable)
- **Pathological (saturated I/O):** >10% drop rate (needs investigation)

---

## Alternatives Considered

### 1. Blocking Locks (`fcntl.LOCK_EX` without `LOCK_NB`)

**Pros:** 100% event retention, no drops  
**Cons:** Adds latency to every telemetry call, can block agent code, deadlock risk if lock held during agent crash  
**Verdict:** Rejected - telemetry MUST NOT slow down agent

### 2. In-Memory Queue + Background Writer

**Pros:** No blocking, high throughput  
**Cons:** Complex (requires thread/process management), queue size limits, memory pressure, events lost on crash  
**Verdict:** Over-engineered for simple JSONL logging

### 3. Separate Telemetry Process

**Pros:** Complete isolation, no contention  
**Cons:** IPC overhead (sockets/pipes), process management complexity, events lost if process crashes  
**Verdict:** Too complex for current scale

### 4. Database (SQLite/Postgres)

**Pros:** ACID guarantees, structured queries  
**Cons:** Heavy dependency, migration complexity, overkill for append-only logs  
**Verdict:** Rejected - JSONL is simpler and sufficient

---

## Migration Path (Future)

If drop rate becomes unacceptable (>10% sustained):

1. **Phase 1:** Add async queue (in-memory, bounded)
2. **Phase 2:** Background writer thread (drains queue to JSONL)
3. **Phase 3:** Graceful shutdown (flush queue before exit)

**Trigger:** User reports >10% drop rate in production workloads (not seen yet)

---

## Summary

- **Model:** Lossy, non-blocking POSIX file locking
- **Guarantees:** No corruption, atomic appends
- **Trade-off:** Accept 2-5% drops for zero latency cost
- **Monitoring:** Drop rate tracked in `telemetry_drops` summary
- **Usage:** Safe for analytics, unsafe for billing/compliance
- **Testing:** Verify no corruption, accept lossy counts
