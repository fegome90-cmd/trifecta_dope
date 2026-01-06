# Field Exercises v1 - Evaluation Results

**Date**: 2026-01-06  
**Dataset**: 20 real-world queries  
**Modes**: OFF (--no-lint) vs ON (TRIFECTA_LINT=1)

---

## Metrics

| Metric | OFF | ON | Delta |
|--------|-----|----|----- |
| Zero-hit rate | 0.0% | 0.0% | +0.0% |
| Avg hits per query | 9.30 | 9.40 | +0.10 |
| Total hits | 186 | 188 | +2 |
| Queries with 0 hits | 0/20 | 0/20 | +0 |

---

## Gate Status

**Zero-hit rate ON**: 0.0%  
**Threshold**: < 30%  
**Status**: ✅ PASS

---

## Query Breakdown

### Queries with 0 hits (ON mode)

✅ No queries with 0 hits!


### Top Performers (ON mode)

- **FE-001** (technical): "How does ValidateContextPackUseCase verify file hashes?" → 10 hits
- **FE-002** (technical): "What is the LSP daemon lifecycle and shutdown sequence?" → 10 hits
- **FE-004** (technical): "What schema validation does ctx_backlog_validate.py perform?" → 10 hits
- **FE-005** (technical): "How does the query linter expand aliases and anchors?" → 10 hits
- **FE-006** (technical): "What telemetry events are tracked in context pack operations?" → 10 hits

---

## Recommendations

✅ Search quality meets threshold. System is performing well on real-world queries.

✅ Linter improves search: +0.10 avg hits per query

---

**END OF REPORT**
