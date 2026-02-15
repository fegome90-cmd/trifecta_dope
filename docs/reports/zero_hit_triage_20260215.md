# Zero-Hit Triage Report

**Date**: 2026-02-15  
**Source**: `_ctx/telemetry/zero_hits.ndjson` + events.jsonl

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total searches | 1,279 |
| Total zero-hits | 318 |
| **Zero-hit ratio** | **24.9%** |

> Note: Previous 53.7% was misleading (tracked only fixture queries)

### By Source

| Source | Searches | Zero-hits | Ratio |
|--------|----------|-----------|-------|
| unknown (agents) | 713 | 185 | 25.9% |
| fixture (tests) | 564 | 132 | 23.4% |
| interactive | 2 | 1 | 50.0% |

---

## Classification Table

| Rank | Count | Query | Bucket | Root Cause | Action |
|------|-------|-------|--------|------------|--------|
| 1 | 100 | `` (empty) | 🧹 **Noise** | Bug: empty query passed to search | Fix: filter empty queries before search |
| 2 | 61 | `servicio` | ✅ **Legítimo miss** | Spanish word, pack is English | No action (expected) |
| 3 | 12 | `servicios` | ✅ **Legítimo miss** | Spanish word | No action |
| 4 | 12 | `búsqueda` | ✅ **Legítimo miss** | Spanish word | No action |
| 5 | 12 | `services` | ✅ **Legítimo miss** | English synonym | No action |
| 6 | 12 | `stop_reason` | ✅ **Legítimo miss** | Internal term | No action |
| 7 | 12 | `123`, `!!!`, `@#$%` | 🧹 **Noise** | Test fixture edge cases | No action (by design) |
| 8 | 12 | `UPPERCASE`, `MixedCase` | 🧹 **Noise** | Test fixture case sensitivity | No action (by design) |
| 9 | 11 | `config` | ✅ **Was miss** | Previously not in pack | **RESOLVED** - now returns hits |
| 10 | 10 | `ContextService` | 📦 **Pack faltante** | In pack (22 refs) but not found | **INVESTIGATE** - case/score issue |

---

## Key Findings

### 1. Empty Query is the Biggest Issue
- **100 zero-hits** from empty queries (31% of all zero-hits!)
- Source: "unknown" (agents calling search without query)
- **GOOD NEWS**: B2 intervention (query validation) already implemented
- **Evidence**: 62 queries rejected (not counted as zero-hits):
  - 38x: "Query cannot be empty or whitespace-only"
  - 24x: "Query must be at least 2 characters"

### 2. Spanish Words Are Legitimate Misses
- `servicio`, `servicios`, `búsqueda` = 85 zero-hits
- Pack is English-indexed, these are expected misses
- **Action**: None (by design)

### 3. Test Fixture is Working as Intended
- 132 zero-hits from fixture (test edge cases)
- **Action**: None (by design)

### 4. ContextService is a Real Issue
- Exists in context pack (22 references)
- But search returns 0 hits
- **Action**: Investigate - possibly needs anchor or different indexing

---

## Intervention Plan

### Priority 1: Filter Empty Queries
```python
# In CLI or search use case
if not query.strip():
    raise ValueError("Empty query not allowed")
```

### Priority 2: ContextService - INVESTIGATED

**Finding**: The file IS in the pack (`repo:src/application/context_service.py:299a315568`) but search returns 0 hits.

**Root Cause**: The chunk text starts with the docstring. The class name `ContextService` only appears in code (`class ContextService:`), not in the searchable text.

**Solution Applied**: Added ContextService keyword to docstring

```python
# Before
"""Service for Programmatic Context Calling logic."""

# After  
"""Service for Programmatic Context Calling logic (ContextService)."""
```

**Reality Check (AFTER FIX)**:
```
$ trifecta ctx search -s . -q "ContextService" --limit 3
Search Results (1 hits):
1. [repo:src/application/context_service.py:1f6cec8071] context_service.py
   Score: 0.50 | Tokens: ~2824
```

**Status**: ✅ FIXED - now returns 1 hit

---

## Reality Check Results

| Query | Before | After | Status |
|-------|--------|-------|--------|
| `config` | 0 hits | 3 hits | ✅ Fixed |
| `ContextService` | 0 hits | 0 hits | ❌ Still broken |

---

## Success Criteria

- [ ] Filter empty queries → saves 100 zero-hits → ratio 24.9% → 17.1%
- [ ] Fix ContextService → saves 10 zero-hits → 17.1% → 16.3%
- [ ] **Target**: < 20% zero-hit ratio

---

## Next Steps

1. Create fix for empty query filtering
2. Investigate ContextService indexing
3. Re-run telemetry after fixes
4. Measure new ratio
