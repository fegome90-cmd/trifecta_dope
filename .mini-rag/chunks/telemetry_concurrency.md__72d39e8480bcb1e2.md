## Model Overview

Trifecta telemetry uses **POSIX `fcntl.flock()`** with `LOCK_EX | LOCK_NB` (exclusive, non-blocking) for concurrent writes to JSONL files.

```python
import fcntl

def _write_jsonl(self, filename: str, data: Dict[str, Any]) -> bool:
    """
    Write event to JSONL. Returns False if lock cannot be acquired (lossy).
    """
    try:
        with open(path, "a") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            f.write(json.dumps(data) + "\n")
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        return True
    except BlockingIOError:
        return False  # Lock contention - skip this event (lossy)
```

---
