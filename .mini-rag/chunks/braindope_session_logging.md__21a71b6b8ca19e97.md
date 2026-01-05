### Schema Validado
```json
{
  "ts": "2026-01-04T11:00:00-03:00",
  "run_id": "run_X",
  "segment_id": "abc123",
  "cmd": "session.entry",
  "args": {
    "summary": "Fixed bug X",
    "type": "debug|develop|document|refactor",
    "files": ["a.py", "b.py"],
    "commands": ["pytest", "ruff check"]
  },
  "result": {"outcome": "success|partial|failed"},
  "timing_ms": 0,
  "warnings": [],
  "x": {"tags": ["tag1", "tag2"]}
}
```
