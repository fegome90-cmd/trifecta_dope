### A.4 Concurrency & Locking

**Lock Mechanism:** POSIX fcntl (non-blocking, fail-safe)

**Code:** `telemetry.py` lines 258-276:
```python
def _write_jsonl(self, filename: str, data: Dict[str, Any]) -> None:
    """Append to JSONL with rotation and locking."""
    path = self.telemetry_dir / filename
    self._rotate_if_needed(path)

    import fcntl
    try:
        with open(path, "a", encoding="utf-8") as f:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except (IOError, OSError):
                # Lock busy: skip write to avoid corruption
                print("Telemetry skipped: lock busy", file=sys.stderr)
                self.warnings.append("telemetry_lock_skipped")
                return  # ← SKIP WRITE if busy (fail-safe, lossy)
```

**Behavior:**
- Non-blocking lock (LOCK_NB); if lock held, skip write and log warning
- **This is LOSSY**: If concurrent writes happen, some events are dropped
- **Acceptable for**: Sampling-grade telemetry (metrics counters)
- **NOT acceptable for**: Critical events (LSP ready, command boundaries, bytes_read)

**Mitigation for MVP:** Use existing `telemetry.event()` which uses this lock, but add a **fallback queue** for critical events (see Phase B).
