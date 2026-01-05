```markdown
# Telemetry Event Schema (AST+LSP)

**Version:** 1.0 (PR#1)  
**Status:** Specification (implementation in PR#2)

---

## Event Types

### 1. AST Events

| Event Type | Fields | Example |
|------------|--------|---------|
| `ast.parse` | `file` (relative), `status`, `functions_count`, `classes_count`, `skeleton_bytes`, `reduction_ratio`, `cache_hit` | `{"cmd": "ast.parse", "args": {"file": "src/domain/models.py"}, "result": {"status": "ok", "functions": 3, "classes": 2}, "timing_ms": 45, "x": {"skeleton_bytes": 512, "reduction_ratio": 0.08, "cache_hit": false}}` |

### 2. LSP Events

**State Machine:**
- **COLD**: No LSP process spawned
- **WARMING**: Process spawned, initializing (parallel with AST build)
- **READY**: Initialized + first notification received (publishDiagnostics or similar)
- **FAILED**: Spawn/init error or crash

| Event Type | Fields | Example |
|------------|--------|---------|
| `lsp.spawn` | `pyright_binary`, `subprocess_pid`, `status` | `{"cmd": "lsp.spawn", "args": {"pyright_binary": "pyright-langserver"}, "result": {"subprocess_pid": 12345, "status": "ok"}, "timing_ms": 0, "x": {"lsp_state": "WARMING"}}` |
| `lsp.state_change` | `from_state`, `to_state`, `reason` | `{"cmd": "lsp.state_change", "args": {}, "result": {"from_state": "WARMING", "to_state": "READY", "reason": "publishDiagnostics received"}, "timing_ms": 1500}` |
| `lsp.request`
