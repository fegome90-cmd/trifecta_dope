### Task 3: Claude Code CLI wrapper (pre/post hooks)

**Files:**
- Create: `scripts/claude_code_wrapper.py`
- Create: `bin/cc`
- Modify: `readme_tf.md`
- Modify: `skill.md`

**Step 1: Write failing test**

```python
# tests/unit/test_claude_wrapper.py

def test_wrapper_fail_closed_when_post_hook_fails(tmp_path, monkeypatch):
    # Simulate session write error
    result = run_wrapper_with_error()
    assert result.exit_code != 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_claude_wrapper.py -v`
Expected: FAIL (wrapper not implemented).

**Step 3: Write minimal implementation**

```python
# scripts/claude_code_wrapper.py
# 1) pre-hook: resolve segment + session path
# 2) run Claude CLI, capture output
# 3) post-hook: append run record + ctx sync + ctx validate
# 4) fail-closed if any step fails
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_claude_wrapper.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add scripts/claude_code_wrapper.py bin/cc tests/unit/test_claude_wrapper.py readme_tf.md skill.md
git commit -m "feat: add claude cli wrapper with pre/post hooks"
```
