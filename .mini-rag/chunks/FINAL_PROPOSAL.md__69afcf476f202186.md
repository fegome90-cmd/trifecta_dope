### Event Raw (en telemetry.jsonl)
```json
{
  "ts": "2026-01-04T11:00:00-03:00",
  "cmd": "session.entry",
  "args": {
    "summary": "Fixed LSP daemon lifecycle",
    "type": "debug",
    "files": ["src/infrastructure/lsp_client.py"],
    "commands": ["pytest tests/integration/"]
  },
  "result": {"outcome": "success"},
  "x": {"tags": ["lsp", "daemon"]}
}
```

**Campos ELIMINADOS del output**:
- `run_id` (irrelevante para session context)
- `segment_id` (ya conocido por CLI)
- `timing_ms` (siempre 0 para session)
- `warnings` (siempre vacío para session)
