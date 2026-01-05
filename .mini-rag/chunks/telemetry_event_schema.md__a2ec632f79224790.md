### 2. LSP Events

**State Machine:**
- **COLD**: No LSP process spawned
- **WARMING**: Process spawned, initializing (parallel with AST build)
- **READY**: Initialized + `didOpen` + `publishDiagnostics` received
- **FAILED**: Spawn/init error or crash

| Event Type | Fields | Example |
|------------|--------|---------|
| `lsp.spawn` | `pyright_binary`, `subprocess_pid`, `status` | `{"cmd": "lsp.spawn", "args": {"pyright_binary": "pyright-langserver"}, "result": {"subprocess_pid": 12345, "status": "ok"}, "timing_ms": 0, "x": {"lsp_state": "WARMING"}}` |
| `lsp.state_change` | `from_state`, `to_state`, `reason` | `{"cmd": "lsp.state_change", "args": {}, "result": {"from_state": "WARMING", "to_state": "READY", "reason": "publishDiagnostics received"}, "timing_ms": 1500, "x": {}}` |
| `lsp.request` | `method`, `file` (relative), `line`, `col`, `resolved` | `{"cmd": "lsp.request", "args": {"method": "definition", "file": "src/app.py", "line": 42, "col": 10}, "result": {"resolved": true, "target_file": "src/lib.py", "target_line": 15}, "timing_ms": 120, "x": {}}` |
| `lsp.fallback` | `reason`, `fallback_to` | `{"cmd": "lsp.fallback", "args": {"reason": "lsp_not_ready"}, "result": {"fallback_to": "ast_only"}, "timing_ms": 0, "x": {}}` |
