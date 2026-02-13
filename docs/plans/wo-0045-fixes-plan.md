# WO-0045: Code Review Fixes Plan

Generated: 2026-02-13
Based on: Multi-agent code review (4 agents: General, Test Coverage, Error Handling, Simplification)

---

## Priority Classification

| Priority | Criteria | Count |
|----------|----------|-------|
| P0 - Critical | Runtime errors, security issues, broken functionality | 4 |
| P1 - Important | Missing tests, poor error handling, data loss risk | 6 |
| P2 - Enhancement | Code quality, simplification, test improvements | 4 |

---

## P0: Critical Fixes (BLOCKING)

### Fix 1: Add `is_ok()` helper to result.py
**File:** `src/domain/result.py`
**Severity:** CRITICAL (95% confidence)
**Impact:** `ctx_wo_finish.py` fails to import - entire script broken

**Current State:**
```python
# ctx_wo_finish.py line 22 imports non-existent function:
from src.domain.result import Result, Ok, Err, is_ok
```

**Fix:**
```python
# Add to src/domain/result.py after class definitions:
def is_ok(result: Result[T, E]) -> bool:
    """Type guard to check if a Result is Ok."""
    return result.is_ok()
```

**Verification:**
```bash
uv run python -c "from src.domain.result import is_ok; print('OK')"
```

---

### Fix 2: Add `execution` property to schema
**File:** `docs/backlog/schema/work_order.schema.json`
**Severity:** CRITICAL (95% confidence)
**Impact:** Schema validation passes malformed execution sections

**Current State:**
- `execution` in `required` array but no property definition
- `additionalProperties: true` allows any object

**Fix:**
```json
"execution": {
  "type": "object",
  "required": ["engine", "required_flow", "segment"],
  "properties": {
    "engine": {"type": "string", "const": "trifecta"},
    "required_flow": {"type": "array", "items": {"type": "string"}, "minItems": 1},
    "segment": {"type": "string"}
  },
  "additionalProperties": true
}
```

**Verification:**
```bash
uv run pytest tests/unit/test_wo_trifecta_contract.py -v
```

---

### Fix 3: Remove or clarify `prevent_manual_wo_closure.sh`
**File:** `_ctx/jobs/pending/WO-0045.yaml`
**Severity:** CRITICAL (90% confidence)
**Impact:** WO scope references non-existent deliverable

**Options:**
1. Create the script if needed for WO completion
2. Remove from scope/deliverables if out of scope

**Decision Required:** User to decide

---

### Fix 4: Add error handling to `load_yaml()`
**File:** `scripts/ctx_wo_finish.py`
**Severity:** CRITICAL (90% confidence)
**Impact:** Script crashes on malformed YAML or file errors

**Current State:**
```python
def load_yaml(path: Path) -> dict[str, object] | None:
    return yaml.safe_load(path.read_text())
```

**Fix:**
```python
def load_yaml(path: Path) -> dict[str, object] | None:
    """Load YAML file, returning None for empty files."""
    try:
        if not path.exists():
            return None
        content = path.read_text()
        if not content.strip():
            return None
        data = yaml.safe_load(content)
        return data if isinstance(data, dict) else None
    except (yaml.YAMLError, OSError, PermissionError) as e:
        logger.error(f"Failed to load YAML from {path}: {e}")
        return None
```

**Verification:**
```bash
uv run pytest tests/unit/test_wo_finish_validators.py -v
```

---

## P1: Important Fixes

### Fix 5: Add file read error handling in `validate_minimum_evidence()`
**File:** `scripts/ctx_wo_finish.py:422-423`
**Severity:** HIGH (85% confidence)

**Fix:**
```python
try:
    verdict_content = verdict_path.read_text()
    verdict = json.loads(verdict_content)
except PermissionError:
    return Err(f"EVIDENCE_INVALID: cannot read verdict.json (permission denied): {verdict_path}")
except OSError as e:
    return Err(f"EVIDENCE_INVALID: cannot read verdict.json (I/O error): {e}")
except json.JSONDecodeError as e:
    return Err(f"EVIDENCE_INVALID: verdict.json is malformed: {e}")
```

---

### Fix 6: Add unit tests for `render_error_card()`
**File:** `tests/unit/test_error_cards.py` (NEW)
**Severity:** HIGH (95% confidence)

**Test File:**
```python
"""Unit tests for error_cards.py module."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from cli.error_cards import render_error_card


def test_render_error_card_stable_markers():
    """Verify all stable markers are present for grep assertions."""
    card = render_error_card(
        error_code="TEST_CODE",
        error_class="TEST_CLASS",
        cause="Test cause",
        next_steps=["Step 1", "Step 2"],
        verify_cmd="test --cmd",
    )
    assert "TRIFECTA_ERROR_CODE: TEST_CODE" in card
    assert "CLASS: TEST_CLASS" in card
    assert "NEXT_STEPS:" in card
    assert "VERIFY:" in card


def test_render_error_card_empty_next_steps():
    """Verify empty next_steps list doesn't crash."""
    card = render_error_card(
        error_code="CODE",
        error_class="CLASS",
        cause="Cause",
        next_steps=[],
        verify_cmd="cmd",
    )
    assert "TRIFECTA_ERROR_CODE: CODE" in card


def test_render_error_card_unicode():
    """Verify Unicode in error messages works."""
    card = render_error_card(
        error_code="UNICODE_TEST",
        error_class="VALIDATION",
        cause="Error: ñoño 友達 🎉",
        next_steps=["Fix the ñ"],
        verify_cmd="test",
    )
    assert "ñoño" in card
```

---

### Fix 7: Fix inconsistent error code in evidence validation
**File:** `scripts/ctx_wo_finish.py:654-668`
**Severity:** HIGH (85% confidence)

**Current State:** Always uses `EVIDENCE_MISSING` even for `EVIDENCE_INVALID` errors

**Fix:**
```python
evidence_err = evidence_result.unwrap_err()
error_code = "EVIDENCE_INVALID" if "EVIDENCE_INVALID" in evidence_err else "EVIDENCE_MISSING"
print_error_card(
    error_code=error_code,
    error_class="VALIDATION",
    cause=evidence_err,
    # ...
)
```

---

### Fix 8: Log exceptions instead of silent catch in `inspect_nonrunning_state()`
**File:** `scripts/ctx_wo_finish.py:173-176`
**Severity:** HIGH (85% confidence)

**Current State:**
```python
try:
    state_data = load_yaml(state_path) or {}
except Exception:
    state_data = {}  # Silent swallow
```

**Fix:**
```python
try:
    state_data = load_yaml(state_path)
    if state_data is None:
        state_data = {}
except yaml.YAMLError as e:
    logger.warning(f"Corrupted YAML in {state_path}: {e}")
    state_data = {"_parse_error": str(e)}
except Exception as e:
    logger.warning(f"Cannot read {state_path}: {e}")
    state_data = {}
```

---

### Fix 9: Catch specific exceptions in `generate_artifacts()`
**File:** `scripts/ctx_wo_finish.py:330-334`
**Severity:** HIGH (80% confidence)

**Fix:**
```python
except subprocess.TimeoutExpired as e:
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    return Err(f"ARTIFACT_TIMEOUT: {e.cmd} timed out after {e.timeout}s")
except OSError as e:
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    return Err(f"ARTIFACT_IO_ERROR: {type(e).__name__}: {e}")
except Exception as e:
    import traceback
    traceback.print_exc()
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    return Err(f"ARTIFACT_UNEXPECTED_ERROR: {type(e).__name__}: {e}")
```

---

### Fix 10: Fix weak test assertion
**File:** `tests/unit/test_wo_finish_requires_evidence.py:179-194`
**Severity:** HIGH (90% confidence)

**Current State:**
```python
assert result.is_ok() or result.is_err()  # Always passes!
```

**Fix:**
```python
def test_verdict_without_status_passes(self, tmp_path):
    """verdict.json status field is NOT required by validate_minimum_evidence()."""
    from ctx_wo_finish import validate_minimum_evidence

    handoff_dir = tmp_path / "_ctx" / "handoff" / "WO-TEST"
    handoff_dir.mkdir(parents=True)

    verdict = {"wo_id": "WO-TEST"}  # No status - should pass
    (handoff_dir / "verdict.json").write_text(json.dumps(verdict))

    result = validate_minimum_evidence("WO-TEST", tmp_path)
    assert result.is_ok(), "status field is not required for minimum evidence"
```

---

## P2: Enhancements (Optional)

### Enhancement 1: Simplify `validate_trifecta_contract()`
**File:** `scripts/ctx_wo_take.py:39-70`
**Effort:** Low | **Impact:** Medium

Combine related checks to reduce visual noise:
```python
# Validate required_flow (combine None + type + length check)
required_flow = execution.get("required_flow")
if not isinstance(required_flow, list) or len(required_flow) == 0:
    return Err("TRIFECTA_CONTRACT_INVALID: execution.required_flow must be a non-empty list")
```

---

### Enhancement 2: Module-level imports in test files
**File:** `tests/unit/test_wo_trifecta_contract.py`
**Effort:** Low | **Impact:** Low

Move repeated imports to module level for cleaner code.

---

## Execution Order

1. **P0 Fixes** (Must complete before any testing):
   - [ ] Fix 1: Add `is_ok()` to result.py
   - [ ] Fix 2: Add `execution` property to schema
   - [ ] Fix 3: Decide on `prevent_manual_wo_closure.sh`
   - [ ] Fix 4: Add error handling to `load_yaml()`

2. **Verification after P0:**
   ```bash
   uv run pytest tests/unit/test_wo_*.py -v
   bash scripts/smoke_wo_trifecta_flow.sh WO-0045
   ```

3. **P1 Fixes** (Can be done incrementally):
   - [ ] Fix 5: File read error handling
   - [ ] Fix 6: `render_error_card()` tests
   - [ ] Fix 7: Inconsistent error codes
   - [ ] Fix 8: Log exceptions instead of silent catch
   - [ ] Fix 9: Specific exception catching
   - [ ] Fix 10: Fix weak test assertion

4. **P2 Enhancements** (Optional):
   - [ ] Enhancement 1: Simplify validation functions
   - [ ] Enhancement 2: Module-level imports

---

## Decision Required

**Fix 3** requires user decision:
- Create `prevent_manual_wo_closure.sh` script, OR
- Remove from WO-0045 scope/deliverables

---

## Estimated Effort

| Priority | Estimated Time | LOC Impact |
|----------|----------------|------------|
| P0 | 30 minutes | +50 LOC |
| P1 | 60 minutes | +80 LOC |
| P2 | 20 minutes | -10 LOC (refactor) |
| **Total** | **~2 hours** | **+120 LOC** |
