### Architecture Constraints

- **Single telemetry system:** Reuse `_ctx/telemetry/` directory, no new sinks
- **Monotonic clocks:** `time.perf_counter_ns()` for all latencies
- **Lossy concurrency:** fcntl non-blocking lock (acceptable <2% drop rate for analytics, not gates)
- **Security:** Relative paths only, no file content, reserved key protection
- **AST-first:** Symbol resolution works without LSP; LSP enhances when READY

**Breaking changes:** None. All changes are additive and backward compatible.

---
