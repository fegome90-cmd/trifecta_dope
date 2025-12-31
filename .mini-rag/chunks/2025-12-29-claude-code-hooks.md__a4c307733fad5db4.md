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
