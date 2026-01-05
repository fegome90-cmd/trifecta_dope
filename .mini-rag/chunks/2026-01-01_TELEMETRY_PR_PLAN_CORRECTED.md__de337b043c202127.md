```markdown
# Telemetry Concurrency Model

**Version:** 1.0  
**Status:** Current (PR#1)

---

## Model: Lossy fcntl (Non-Blocking)

**Current Implementation:** `src/infrastructure/telemetry.py` uses POSIX `fcntl.flock()` with `LOCK_EX | LOCK_NB` for file writes.

**Behavior:**
- If lock is available: write succeeds
- If lock is held by another process: write is **skipped** (event lost)
- No blocking, no retries

**Guarantees:**
- ✅ No deadlocks
- ✅ No corruption (atomic append to JSONL)
- ❌ Not lossless (2-5% event drop under concurrent load)

**Usage Policy:**
- **Safe for analytics:** Percentiles, counters, trends are statistically valid despite loss
- **Unsafe for gates:** Do NOT use telemetry counters for critical decisions (e.g., "if lsp_ready_count == 0 then fail")
- **Warning emitted:** `telemetry_lock_skipped` counter tracks dropped events

---

## Alternatives (Not Implemented)

### Single-Writer with Queue
- Spawn background thread/process as telemetry sink
- All events pushed to queue, single writer drains queue
- **Pros:** Zero loss, exact counts
- **Cons:** Complexity (thread lifecycle, shutdown), memory (unbounded queue)

### Blocking Lock
- Use `fcntl.flock(LOCK_EX)` without `LOCK_NB` (blocking wait)
- **Pros:** No loss
- **Cons:** Performance impact (waits for lock), potential deadlock if writer crashes

---

## Decision: Lossy Model is Correct

**Rationale:**
