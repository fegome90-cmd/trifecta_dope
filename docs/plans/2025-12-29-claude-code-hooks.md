# Claude Code CLI Hooks Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a reliable pre/post hook flow for Claude Code CLI that always updates `session_ast.md`, gates on `trifecta ctx sync/validate`, and fail-closes on errors.

**Architecture:** Implement a wrapper launcher that intercepts Claude CLI runs, writes a structured Run Record into `_ctx/session_<segment>.md` with locking, and enforces sync/validate. Add a CI gate to ensure session updates accompany code/doc changes.

**Tech Stack:** Python (wrapper + session writer), shell launcher, existing Trifecta CLI, pytest.

### Task 1: Define the Run Record schema + update session template

**Files:**
- Modify: `src/infrastructure/templates.py`
- Modify: `tests/unit/test_session_protocol_templates.py`
- Optional Docs: `readme_tf.md`

**Step 1: Write failing test**

```python
# tests/unit/test_session_protocol_templates.py

def test_session_template_includes_run_record_schema():
    content = TemplateRenderer().render_session(config)
    assert "Run Record Schema" in content
    assert "run_id" in content
    assert "trifecta_sync" in content
    assert "final_status" in content
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_session_protocol_templates.py -v`
Expected: FAIL with missing schema headings/fields.

**Step 3: Write minimal implementation**

```python
# src/infrastructure/templates.py
## Run Record Schema (append-only)
# - run_id
# - timestamp_start / timestamp_end / duration_ms
# - segment / invocation
# - user_intent / actions_summary
# - files_touched / commands_executed / tests_or_checks
# - trifecta_sync / trifecta_validate
# - lock / final_status
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_session_protocol_templates.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/infrastructure/templates.py tests/unit/test_session_protocol_templates.py readme_tf.md
git commit -m "docs: add session run record schema"
```

### Task 2: Implement session writer + lock handling (core hook engine)

**Files:**
- Create: `src/infrastructure/session_writer.py`
- Create: `tests/unit/test_session_writer.py`

**Step 1: Write failing tests**

```python
# tests/unit/test_session_writer.py

def test_acquire_lock_blocks_when_taken(tmp_path):
    lock = tmp_path / ".autopilot.lock"
    lock.write_text("pid: 123")
    with pytest.raises(LockError):
        acquire_lock(lock, timeout_sec=1)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_session_writer.py -v`
Expected: FAIL (module not found / lock behavior missing).

**Step 3: Write minimal implementation**

```python
# src/infrastructure/session_writer.py
class LockError(Exception):
    pass

def acquire_lock(path: Path, timeout_sec: int = 3) -> None:
    # Create lock atomically; fail if exists and not stale
    ...

def append_run_record(session_path: Path, record: dict) -> None:
    # Append a YAML block or markdown section
    ...
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_session_writer.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/infrastructure/session_writer.py tests/unit/test_session_writer.py
git commit -m "feat: add session writer with locking"
```

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

### Task 6: Operational docs + usage contract

**Files:**
- Create: `docs/ops/claude-code-wrapper.md`
- Modify: `README.md`
- Modify: `readme_tf.md`

**Step 1: Write doc changes**

```md
# Claude Code Wrapper
- Install: ln -s $(pwd)/bin/cc ~/.local/bin/cc
- Usage: cc <claude args>
- Guarantees: session update + ctx sync/validate + fail-closed
```

**Step 2: Verify docs render**

Run: `rg -n "cc " README.md readme_tf.md docs/ops/claude-code-wrapper.md`
Expected: references to wrapper and guarantees.

**Step 3: Commit**

```bash
git add docs/ops/claude-code-wrapper.md README.md readme_tf.md
git commit -m "docs: add claude wrapper runbook"
```

---

## Validation Checklist

- `pytest tests/unit/test_session_protocol_templates.py -v`
- `pytest tests/unit/test_session_writer.py -v`
- `pytest tests/unit/test_claude_wrapper.py -v`
- `pytest tests/unit/test_ci_session_gate.py -v`
- `make trifecta-validate PATH=<segment>`

## Notes / Assumptions

- Wrapper is the required entry point for Claude Code CLI (fail-closed enforcement).
- CI gate is authoritative for enforcement when local usage is bypassed.
- `session_ast.md` remains append-only; run record entries are the only modification surface.
