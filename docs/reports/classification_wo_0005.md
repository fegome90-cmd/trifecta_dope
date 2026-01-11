# WO-0005 Gate Classification Report

**Classification**: TEST_BROKEN  
**Date**: 2026-01-05  
**WO**: WO-0005 (Evidence Gate global)

---

## Evidence

### Test File
- **Path**: `tests/acceptance/test_pd_evidence_stop_e2e.py`
- **Function**: `test_e2e_evidence_stop_real_cli()`
- **Lines**: 238-267

### Timeline
- **Test added**: Commit `8386f8d` (2026-01-04)
- **BASE_COMMIT**: `bd26190` (before linter integration)
- **First linter commit**: `672a2b8` (2025-12-31)

### Root Cause
Test hard-coded query `"ContextService"` which **does not exist** in the segment's `context_pack.json`.

```python
# Line 240
ids = _search_for_ids(real_segment, "ContextService", limit=3)
```

The search returns 0 IDs, causing assertion failure:
```
AssertionError: No IDs found for query 'ContextService'
```

---

## Classification Determinista

| Criteria | Result |
|----------|--------|
| **Test exists at BASE?** | ❌ NO (added after linter) |
| **Pre-existing?** | ❌ NO (test didn't exist) |
| **Regression?** | ❌ NO (test didn't exist before) |
| **Test broken?** | ✅ YES (assumes non-existent data) |

**Verdict**: TEST_BROKEN

---

## Logs

| Log | Path |
|-----|------|
| HEAD failure | `_ctx/logs/gate_fail_head.log` |
| BASE commit | `_ctx/logs/gate_base_commit.txt` (BASE_COMMIT=bd26190) |
| After fix | `_ctx/logs/gate_after_fix.log` |
| Full gate | `_ctx/logs/gate_full_after_fix.log` |
| Classification evidence | `/tmp/tf_gate_base.log` |

---

## Fix Applied

**File**: `tests/acceptance/test_pd_evidence_stop_e2e.py`  
**Lines modified**: 240, 259  
**Change**: 
```diff
- ids = _search_for_ids(real_segment, "ContextService", limit=3)
+ ids = _search_for_ids(real_segment, "context", limit=3)
```

```diff
-            "ContextService",
+            "context",
```

**Rationale**: Query `"context"` exists in segment's context_pack.json and returns results.

---

## Verification

**Before fix**:
```bash
$ uv run pytest -q tests/acceptance/test_pd_evidence_stop_e2e.py::test_e2e_evidence_stop_real_cli
F [FAIL]
AssertionError: No IDs found for query 'ContextService'
```

**After fix**:
```bash
$ uv run pytest -q tests/acceptance/test_pd_evidence_stop_e2e.py::test_e2e_evidence_stop_real_cli
. [100%]
1 passed in 0.32s
```

**Full gate**:
```bash
$ uv run pytest -q
482 passed, 1 skipped in 13.48s
```

---

## Final Verdict

**PASS**: 482 tests passed, 0 failures

The test was broken due to incorrect assumption about available data. Fix is minimal (2 lines) and deterministic. Gate is now clean.

---

**Generated**: 2026-01-05 18:40 UTC  
**Status**: COMPLETE
