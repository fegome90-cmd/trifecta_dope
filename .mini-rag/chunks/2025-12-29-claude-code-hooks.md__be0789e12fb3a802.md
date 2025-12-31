### Task 4: Escape hatch + circuit breaker policy (phase 1 scaffolding)

**Files:**
- Modify: `scripts/claude_code_wrapper.py`
- Modify: `docs/ops/claude-code-wrapper.md`

**Step 1: Write failing test**

```python
# tests/unit/test_claude_wrapper.py

def test_bypass_records_audit_entry(monkeypatch):
    monkeypatch.setenv("TRIFECTA_UNSAFE_BYPASS", "1")
    result = run_wrapper_bypass()
    assert "BYPASS" in result.session_entry
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_claude_wrapper.py -v`
Expected: FAIL.

**Step 3: Write minimal implementation**

```python
# scripts/claude_code_wrapper.py
if os.getenv("TRIFECTA_UNSAFE_BYPASS") == "1":
    record["final_status"] = "BYPASS"
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_claude_wrapper.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add scripts/claude_code_wrapper.py docs/ops/claude-code-wrapper.md tests/unit/test_claude_wrapper.py
git commit -m "feat: add bypass audit entry"
```
