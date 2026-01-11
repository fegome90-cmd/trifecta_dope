### C. TIMING PRECISION: MONOTONIC CLOCK READY

**Current:** `time.time()` (wall-clock) used in cli.py:279
```python
start_time = time.time()
# ... operation ...
telemetry.observe("ctx.search", int((time.time() - start_time) * 1000))
```

**Issue:** `time.time()` can jump backward (NTP adjustments).

**Solution:** Use `time.perf_counter_ns()` for AST/LSP relative durations
```python
start_ns = time.perf_counter_ns()
# ... operation ...
elapsed_ms = int((time.perf_counter_ns() - start_ns) / 1_000_000)
telemetry.observe("lsp.definition", elapsed_ms)
```

**Status:** ✅ Available in Python 3.7+, no new dependencies. Fully backward compatible.
