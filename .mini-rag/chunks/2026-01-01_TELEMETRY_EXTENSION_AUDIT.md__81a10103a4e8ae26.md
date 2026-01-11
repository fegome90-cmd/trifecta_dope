### A.5 Timing Precision

**Current:** Uses `time.time()` wall-clock (millisecond precision)

**Example from cli.py:279:**
```python
start_time = time.time()
# ... operation ...
telemetry.observe("ctx.search", int((time.time() - start_time) * 1000))
```

**Issue:** `time.time()` is affected by NTP adjustments, clock skew, etc.

**For AST/LSP:** MUST use monotonic clock (`time.perf_counter_ns()`) for relative durations.
