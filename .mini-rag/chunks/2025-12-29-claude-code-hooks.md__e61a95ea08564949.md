### Task 5: CI gate for session updates

**Files:**
- Create: `scripts/ci/check_session_update.py`
- Modify: `Makefile`
- Create: `.github/workflows/session-gate.yml`

**Step 1: Write failing test**

```python
# tests/unit/test_ci_session_gate.py

def test_gate_fails_when_code_changes_without_session_update():
    result = run_check_with_diff(["src/app.py"])
    assert result.exit_code == 1
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_ci_session_gate.py -v`
Expected: FAIL.

**Step 3: Write minimal implementation**

```python
# scripts/ci/check_session_update.py
# if git diff includes src/ or docs/ changes, require _ctx/session_*.md touched
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_ci_session_gate.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add scripts/ci/check_session_update.py Makefile .github/workflows/session-gate.yml tests/unit/test_ci_session_gate.py
git commit -m "ci: gate session updates for code/doc changes"
```
