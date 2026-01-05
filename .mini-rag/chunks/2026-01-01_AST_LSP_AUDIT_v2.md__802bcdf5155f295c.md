### PR: Fix Session Append Race Condition

**Issue:** [src/infrastructure/cli.py:1149-1180](src/infrastructure/cli.py#L1149)

```python
# BEFORE (no lock):
def session_append(...):
    session_file = ...
    with open(session_file, "a") as f:  # Concurrent writes → corruption
        f.write(entry)

# AFTER (with lock):
def session_append(...):
    session_file = ...
    lock_file = session_file.parent / f".session_{segment}.lock"
    with file_lock(lock_file):  # Single-writer
        with open(session_file, "a") as f:
            f.write(entry)
```

**Tests:**
- `test_session_append_concurrent_writes_safe`: Spawn 5 threads, each writes 10 entries, verify no corruption
- `test_session_lock_timeout_fails_gracefully`: Lock held >5s, new append fails cleanly

**DoD:**
- [ ] Lock file created in .session_{segment}.lock
- [ ] Concurrent writes blocked (LOCK_EX via fcntl)
- [ ] Timeout 5s; fail loudly if lock held
- [ ] 2 unit tests pass
- [ ] Single commit, merged before AST/LSP sprint starts

---
