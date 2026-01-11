#### C.1.4 File System Adapter

**File:** `src/infrastructure/file_system.py`

**Hook in read methods:**
```python
class FileSystemAdapter:
    def read_file_at_mode(self, path: Path, mode: str) -> str:
        start_ns = time.perf_counter_ns()
        content = self._do_read(path, mode)
        elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000

        bytes_read = len(content.encode('utf-8'))
        self.total_bytes_read += bytes_read

        self.telemetry.incr(f"file_read_{mode}_bytes_total", bytes_read)

        return content
```
