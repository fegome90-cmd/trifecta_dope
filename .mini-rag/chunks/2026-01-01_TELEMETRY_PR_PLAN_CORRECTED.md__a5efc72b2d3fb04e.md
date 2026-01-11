```

---

## Security & Redaction Policy

1. **Paths:** Always use `_relpath(repo_root, path)` to log relative paths. NEVER log absolute paths or URIs with user/system info.
2. **Segment:** Log `segment_id` (SHA-256 hash prefix), not `segment_path` (prevents path leakage).
3. **Content:** Do not log file content. Log hashes (SHA-256), sizes, and line ranges only.
4. **Secrets:** Do not log API keys, tokens, or credentials in any field.
5. **Reserved Keys:** `ts`, `run_id`, `segment_id`, `cmd`, `args`, `result`, `timing_ms`, `tokens`, `warnings`, `x` are protected. Extra fields go under `x` namespace.

---

## LSP READY Definition

**READY state** is achieved when:
1. LSP process spawned successfully
2. `initialize` request sent and `InitializeResult` received
3. `didOpen` sent for 1 file (relevant to current operation)
4. `textDocument/publishDiagnostics` notification received for that specific URI

**Policy:**
- LSP spawns in parallel during AST build (warm-up phase)
- Warm-up sends `didOpen` for first Python file found by AST scan
- READY achieved when `publishDiagnostics` received for that specific URI
- Requests ONLY sent when state == READY
- If not READY when needed → fallback to AST-only (no blocking wait)
- No aggressive timeouts: LSP gets full init time (5-10s typical)
- READY is LSP-instance-specific, not global (multiple LSP clients track own state)
```
