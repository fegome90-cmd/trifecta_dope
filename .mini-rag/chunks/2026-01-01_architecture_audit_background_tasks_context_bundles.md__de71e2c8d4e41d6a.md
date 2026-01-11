### A.3 FileSystemAdapter → File Read Tracking

**Archivo**: `src/infrastructure/file_system.py`

**Punto de inserción**: En `scan_files()` y `read_text()` wrappers.

```python
# file_system.py

class FileSystemAdapter:
    def __init__(self, bundle_recorder=None):
        self.bundle_recorder = bundle_recorder

    def read_text(self, path: Path) -> str:
        content = path.read_text()

        # NUEVO: Log file read to bundle
        if self.bundle_recorder:
            self.bundle_recorder.log_file_read(
                path=str(path),
                lines_read=[1, len(content.splitlines())],
                char_count=len(content)
            )

        return content
```

---
