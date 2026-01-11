### 5. AST Symbols (Code Navigation)

**Command**:
```bash
trifecta ast symbols "sym://python/mod/<module.path>" --segment <path>
```

**What it does**: Returns AST symbols (functions, classes) from Python modules

**Preconditions**:
- Module file must exist in segment
- Python file must be parseable

**Options**:
- `--segment <path>`: Segment path (default: .)
- `--telemetry <level>`: off/lite/full (default: off)

**Example**:
```bash
trifecta ast symbols "sym://python/mod/src.domain.result" --segment /tmp/my_segment
```

**Success**: JSON with symbols

```json
{
  "status": "ok",
  "segment_root": "/tmp/my_segment",
  "file_rel": "src/domain/result.py",
  "symbols": [
    {"kind": "class", "name": "Ok", "line": 22},
    {"kind": "class", "name": "Err", "line": 53}
  ]
}
```

**Error** (if module not found):
```json
{
  "status": "error",
  "error_code": "FILE_NOT_FOUND",
  "message": "Could not find module for src.domain.result"
}
```

---
