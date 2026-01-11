### Single-Writer Lock for Session Append

**Current Problem:**
```python
# src/infrastructure/cli.py:1149-1180
def session_append(...):
    session_file = segment_path / "_ctx" / f"session_{segment_name}.md"
    with open(session_file, "a", encoding="utf-8") as f:  # ← NO LOCK
        f.write("\n".join(entry_lines) + "\n")
```

Concurrent writes → corruption risk.

**Fix (Apply Before MVP):**
```python
def session_append(...):
    session_file = segment_path / "_ctx" / f"session_{segment_name}.md"
    lock_file = session_file.parent / f".session_{segment_name}.lock"

    from src.infrastructure.file_system_utils import file_lock

    with file_lock(lock_file):  # Single-writer enforcement
        with open(session_file, "a", encoding="utf-8") as f:
            f.write("\n".join(entry_lines) + "\n")
```

**Requirement:** Merge this fix before starting AST/LSP sprint.

---
