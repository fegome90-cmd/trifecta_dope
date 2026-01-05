### 3. File Read Events

| Event Type | Fields | Example |
|------------|--------|---------|
| `file.read` | `file` (relative), `mode`, `bytes`, `status` | `{"cmd": "file.read", "args": {"file": "src/app.py", "mode": "excerpt"}, "result": {"bytes": 2048, "status": "ok"}, "timing_ms": 5, "x": {"disclosure_mode": "excerpt"}}` |
