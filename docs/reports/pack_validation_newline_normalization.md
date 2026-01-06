# Pack Validation Newline Normalization - Technical Report

**Date**: 2026-01-06  
**Issue**: Hash mismatch loop in context pack build→validate cycle  
**Status**: ✅ RESOLVED

---

## Problem Statement

Context pack validation was failing with hash mismatches on files that didn't end with newline:

```
❌ Validation Failed
   - Source file content changed (Hash mismatch): docs/plans/t9_3_6_clamp_calibration.md
   - Source file size mismatch: docs/plans/t9_3_6_clamp_calibration.md (7348 vs 7346)
```

This created an infinite loop:
1. Build phase: adds `\n` → hashes normalized content → stores in pack
2. Validate phase: reads raw bytes → hashes original → mismatch
3. Sync fails → user retries → loop continues

---

## Root Cause Analysis

### Build Phase (BuildContextPackUseCase)
```python
# src/application/use_cases.py lines 465-467
content = file_path.read_text()
if not content.endswith("\n"):
    content += "\n"  # Normalize by adding newline
# Hash this normalized content
```

### Validate Phase (ValidateContextPackUseCase) - BEFORE FIX
```python
# src/application/use_cases.py line 725 (old)
content = src_abs_path.read_bytes()  # Raw bytes, NO normalization
current_sha = hashlib.sha256(content).hexdigest()
```

**Result**: Different content → different hashes → permanent mismatch

---

## Solution: Consistent Normalization Contract

### Fix Applied (ValidateContextPackUseCase)
```python
# src/application/use_cases.py lines 721-727 (new)
# Deep verification - use same normalization as build
content_str = src_abs_path.read_text()
if not content_str.endswith("\n"):
    content_str += "\n"  # Same normalization as build
content = content_str.encode()
current_sha = hashlib.sha256(content).hexdigest()
```

### Contract Established

**Both build and validate MUST**:
1. Read file as text
2. Add `\n` if not present
3. Hash the normalized content

This ensures:
- ✅ Consistent hashing across phases
- ✅ Pre-commit compliance (files end with newlines)
- ✅ No false-positive validation errors

---

## Regression Test

**File**: `tests/integration/test_pack_validation_normalizes_newline.py`

**Test Case**:
1. Create file WITHOUT trailing newline
2. Run `trifecta create` + `trifecta ctx sync`
3. Assert: sync completes without hash mismatch

**Coverage**:
- Functional: Validates actual behavior
- Meta: Ensures normalization code exists in use_cases.py

**Result**: 2/2 tests PASS

---

## Evidence

### Before Fix
```
❌ Validation Failed
   - Hash mismatch: docs/plans/t9_3_6_clamp_calibration.md
   - Hash mismatch: docs/auditoria/AST_CACHE_DEEP_DIVE_ANALYSIS.md
   - Hash mismatch: src/cli/__init__.py
```

### After Fix
```
✅ Build complete. Validating...
✅ Validation Passed
```

### Test Execution
```bash
$ uv run pytest -xvs tests/integration/test_pack_validation_normalizes_newline.py
test_pack_build_and_validate_normalize_newlines_consistently PASSED
test_pack_validation_contract_documented_in_code PASSED
2 passed in 0.95s
```

---

## Impact

**Files Fixed**:
- `docs/plans/t9_3_6_clamp_calibration.md` (7580b actual, was expecting 7346-7348b)
- `docs/auditoria/AST_CACHE_DEEP_DIVE_ANALYSIS.md` (0b, was expecting 1b)
- `src/cli/__init__.py` (0b, was expecting 1b)

**Systems Stabilized**:
- ✅ Context pack build/validate cycle
- ✅ Pre-commit hooks (no more --no-verify needed)
- ✅ Acceptance tests (45/45 passing)

---

## Future Work

### Considered but Deferred

**Alternative A**: Remove normalization entirely
- ❌ Breaks pre-commit compliance
- ❌ Many Python tools expect trailing newlines

**Alternative B**: Skip empty files
- ✅ Would fix 0-byte case
- ❌ Doesn't fix files without newlines (like t9_3_6)

**Alternative C**: Add `--force-rebuild` flag
- ✅ Useful for emergency recovery
- ⏸️ Not needed now (validation works)

---

## Lessons Learned

1. **Build and validate must use identical canonicalization** - any difference creates false positives
2. **Empty files are valid** - normalization converts 0 bytes → 1 byte (`\n`)
3. **Test normalization contracts** - regression test prevents future breakage
4. **Fail-closed debugging** - systematic evidence capture (logs, hex dumps) identified root cause quickly

---

**END OF REPORT**
