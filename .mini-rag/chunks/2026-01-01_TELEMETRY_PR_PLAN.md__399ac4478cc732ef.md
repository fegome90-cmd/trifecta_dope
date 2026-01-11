#### File: `src/infrastructure/file_system.py`

**Add bytes tracking:**

```python
class FileSystemAdapter:
    """File system operations with telemetry."""

    def __init__(self):
        self.total_bytes_read = 0  # NEW

    def read_file_at_mode(self, path: Path, mode: Literal["raw", "excerpt", "skeleton"] = "excerpt") -> str:
        """Read file content at disclosure level."""
        start_ns = time.perf_counter_ns()  # NEW

        content = self._do_read(path, mode)

        bytes_read = len(content.encode('utf-8'))
        self.total_bytes_read += bytes_read  # NEW

        if hasattr(self, 'telemetry') and self.telemetry:
            # NEW: Emit per-file read event
            elapsed_ms = int((time.perf_counter_ns() - start_ns) / 1_000_000)

            self.telemetry.event(
                "file.read",
                {"file": str(path.name), "mode": mode},
                {"bytes": bytes_read, "status": "ok"},
                elapsed_ms,
            )

            # NEW: Increment mode-specific counter
            self.telemetry.incr(f"file_read_{mode}_bytes_total", bytes_read)

        return content
```
