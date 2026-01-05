## CRITICAL DESIGN DECISIONS (WITH JUSTIFICATION)

| Decision | Choice | Why Not Alternative |
|----------|--------|-------------------|
| **Timing precision** | perf_counter_ns() | ❌ time.time() affected by NTP; ❌ clock.monotonic() is older (3.3+) |
| **Event format** | Extend event() kwargs | ❌ Don't create new sink; ❌ Don't subclass Telemetry |
| **Aggregation** | Extend last_run.json | ❌ Don't create separate summary file; ❌ metrics.json is for counters only |
| **LSP "ready"** | publish Diagnostics OR definition success | ❌ Don't invent custom LSP request; ❌ Use standard protocol |
| **Fallback strategy** | Tree-sitter on timeout | ❌ Don't retry LSP (2–5s each); ❌ Don't block user (latency first) |
| **Sampling** | No sampling for critical events | ⚠️ Acceptable drop <2%; ✅ Use same fcntl lock for all |
| **Redaction** | Relative paths in telemetry | ❌ No absolute paths (user privacy); ❌ No file content (data safety) |

**All decisions approved.** ✅

---
