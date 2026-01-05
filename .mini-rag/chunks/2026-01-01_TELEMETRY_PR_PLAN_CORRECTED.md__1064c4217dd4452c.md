ter crashes

---

## Decision: Lossy Model is Correct

**Rationale:**
1. Telemetry is for **observability**, not correctness. Losing 2% of events does not materially impact trend analysis.
2. No critical paths depend on telemetry counters (LSP READY is determined by in-memory state, not logs).
3. Simplicity: no background threads, no shutdown complexity.
4. Performance: no blocking waits.

**Test Criteria:**
- Concurrent tests MUST validate **no corruption** (valid JSON, no interleaved writes)
- Concurrent tests MUST NOT expect **exact counts** (some events may be dropped)
- Validate: "All logged events are valid" NOT "All events are logged"
```
