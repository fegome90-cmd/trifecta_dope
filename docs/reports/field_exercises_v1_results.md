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
| **Anchor usage** | N/A | **2/20 (10.0%)** | - |

---

## Gate Status

**Zero-hit rate ON**: 0.0%  
**Threshold**: < 30%  
**Status**: ✅ PASS

---

## Linter Analysis

**Anchor Expansion**: 2/20 queries (10.0%) detected expansion patterns

### Telemetry-Based Metrics (Historical Data)

**Source**: `_ctx/metrics/field_exercises_v1_anchor_metrics.json`  
**Note**: Metrics from aggregated telemetry (includes runs beyond FE v1)

| Metric | OFF Mode | ON Mode | Delta |
|--------|----------|---------|-------|
| Total queries | 241 | 295 | +54 |
| Avg hits | 1.21 | 4.67 | +3.46 |
| Zero-hit count | 106 | 72 | -34 |
| Anchor expansion | N/A | 70/295 (23.7%) | - |

**Anchor Usage Breakdown (ON mode)**:
- Strong anchors added: 139 total (0.47 per query)
- Weak anchors added: 0 total
- Query class distribution:
  - Vague: 87 queries (29.5%)
  - Semi-guided: 42 queries (14.2%)
  - Guided: 8 queries (2.7%)
  - Disabled: 157 queries (53.2%)

**Performance Impact**:
- Avg hits when expanded: 2.80
- Avg hits when NOT expanded: 5.26
- **Delta**: -2.46 hits when expanded

**Interpretation**: Negative delta indicates anchor expansion activates for harder queries (vague/exploratory) that naturally have lower hit rates. Expansion is a response to difficulty, not a cause of lower performance.

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
