## NOTES

1. **No breaking changes:** All existing CLI commands work unchanged.
2. **Backward compatible:** Old code calling `telemetry.event()` without extra fields still works.
3. **Monotonic clocks:** All new timings use `time.perf_counter_ns()`, never `time.time()`.
4. **Secure:** No absolute paths, no file content, no API keys in telemetry.
5. **Auditable:** Every event is append-only; no deletions or modifications.
6. **Drop-safe:** Critical events (lsp.ready, command boundaries) use same lock as everything else; acceptable <2% drop rate.

---

**Plan Complete:** Ready for Day 1 implementation  
**Owner:** Senior Engineer / Telemetry Architect  
**Estimated Duration:** 4–5 days  
**Success Criterion:** All tests pass, no data loss, all metrics queryable from last_run.json
