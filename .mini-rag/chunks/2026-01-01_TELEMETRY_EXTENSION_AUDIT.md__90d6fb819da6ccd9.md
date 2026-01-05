## PHASE G: VALIDATION CRITERIA (PASS/FAIL)

| Criterion | Pass | Status |
|-----------|------|--------|
| **No second telemetry system created** | Only events.jsonl, metrics.json, last_run.json used | ✅ DESIGN COMPLIES |
| **All timings use perf_counter_ns** | No time.time() for intervals | ⏳ IMPLEMENTATION (T-TBD) |
| **No sensitive data logged** | Relative paths only, no file content, no API keys | ⏳ IMPLEMENTATION (T-TBD) |
| **LSP READY clearly defined** | Spec: initialized + (diagnostics OR definition success) | ✅ DESIGN COMPLIES |
| **Critical events not lossy** | lsp.ready, command.end, bytes_read must NOT drop | ⏳ IMPLEMENTATION (needs fallback queue) |
| **Bytes tracked per command** | metrics.json has file_read_*_bytes_total counters | ✅ DESIGN COMPLIES |
| **Fallback rate measurable** | lsp_timeout_count, lsp_fallback_count in summary | ✅ DESIGN COMPLIES |
| **Summary math correct** | p50/p95 calculated correctly on synthetic data | ⏳ TESTING (T-TBD) |
| **All tests pass** | 8 unit + 5 integration tests >80% pass | ⏳ TESTING (T-TBD) |

---
