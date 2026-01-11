## NOTES

1. **No breaking changes:** All existing CLI commands work unchanged.
2. **Backward compatible:** Old code calling `telemetry.event()` without extra fields still works.
3. **Monotonic clocks:** All new timings use `time.perf_counter_ns()`, never `time.time()`.
4. **Secure:** No absolute paths (normalized via `_relpath`), no file content, no API keys in telemetry.
5. **Auditable:** Every event is append-only; no deletions or modifications.
6. **Drop-safe:** Critical decisions (LSP READY) based on in-memory state, not telemetry counters.
7. **Telemetry is for observation, NOT gates:** Use tests/e2e/deterministic outputs for pass/fail decisions. Lossy telemetry is for trends/analytics only.

---

**Plan Complete:** Ready for Day 1 implementation  
**Owner:** Senior Engineer  
**Estimated Duration:** 5-6 days (2 days PR#1 + 3-4 days PR#2)  
**Success Criterion:** All tests pass, no data loss, all metrics queryable from last_run.json
