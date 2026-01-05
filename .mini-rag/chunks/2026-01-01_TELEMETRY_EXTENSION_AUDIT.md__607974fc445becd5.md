### B.5 Monotonic Timing (CRITICAL)

**Use `time.perf_counter_ns()` for all AST/LSP relative durations:**

```python
import time

start_ns = time.perf_counter_ns()  # Monotonic clock, nanoseconds
# ... operation ...
elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000

telemetry.observe("lsp.definition", int(elapsed_ms))
```

**NOT `time.time()` for relative intervals!**

**Store as:** Integer milliseconds in `timing_ms` field (for backward compatibility).

---
