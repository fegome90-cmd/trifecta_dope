# Code Review Report: scripts/debug

**Date:** 2026-01-06
**Scope:** `scripts/debug` directory
**Reviewer:** Antigravity (Superpower V)
**Verdict:** 🟡 **WARN** (Maintenance/Robustness Issues)

## 🚨 Critical Issues (Must Fix)

### 1. Loose Script Pattern (Rule 1 Violation)
**File:** All (`debug_client.py`, `debug_status.py`)
**Violation:** Scripts rely on `sys.path` injection ("Path hack").
**Rule:** `GEMINI.md` Rule 1: "Do not run loose scripts". Use CLI commands or `pytest` harnesses.
**Evidence:**
```python
_script_dir = Path(__file__).parent
_project_root = _script_dir.parent.parent
sys.path.insert(0, str(_project_root))
```
**Remediation:**
- Convert to `eval/scripts/harness_*.py` if meant for verification.
- Run via `uv run python -m scripts.debug.debug_client` to avoid path hacks (requires `__init__.py` which exists).

## ⚠️ Important Issues (Should Fix)

### 1. Fragile Hardcoding
**File:** `debug_client.py`
**Issue:** Hardcoded dependency on `src/infrastructure/cli.py`.
**Risk:** Script breaks if file moves.
**Remediation:** Use dynamic discovery or argument parsing (`sys.argv`).

### 2. Busy Wait Loop
**File:** `debug_client.py`
**Issue:** Loop checks `client.state` without `time.sleep()`.
**Risk:** CPU spin and log spam.
**Remediation:** Add `time.sleep(0.1)` inside the loop.

## Action Plan

1. **Formalize**: Move useful debug logic to `eval/harness/` or `src/cli/debug_commands.py`.
2. **Deprecate**: If `debug_ts.py` is covered by `tests/unit/test_tree_sitter.py`, delete the script.
3. **Refactor**: Remove `sys.path` hacks and run as modules.

---
*Generated via Superpower: code-review-checklist*
