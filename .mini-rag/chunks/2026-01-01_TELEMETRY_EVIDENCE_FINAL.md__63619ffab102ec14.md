### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Monotonic clock unavailable | 🟢 LOW | 🟠 MEDIUM | Python 3.7+ verified; add check in T1 |
| Tree-sitter install fails | 🟢 LOW | 🟠 MEDIUM | Add setup docs; pre-install in CI |
| Concurrent writes corrupt log | 🟠 MEDIUM | 🟢 LOW | Existing fcntl handles; lossy ok for telemetry |
| Telemetry overhead slows CLI | 🟠 MEDIUM | 🟢 LOW | perf_counter_ns is <100ns; negligible |
| LSP timeout doesn't trigger fallback | 🟠 MEDIUM | 🟡 MEDIUM | Mock LSP in tests; validate with real server |
| Relative path redaction incomplete | 🟢 LOW | 🟡 MEDIUM | Code review checklist; grep for "/" in telemetry |
| Summary percentile math wrong | 🟠 MEDIUM | 🟢 LOW | Synthetic validation test; manual spot-check |

**Overall Risk:** 🟢 **LOW TO MEDIUM** (all mitigated, no show-stoppers)

---
