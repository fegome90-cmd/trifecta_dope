## LSP READY Definition (PR#2)

**READY state** is achieved when:
1. LSP process spawned successfully
2. `initialize` request sent and `InitializeResult` received
3. `didOpen` sent for first Python file found by AST scan
4. `textDocument/publishDiagnostics` notification received for that specific URI

**Policy:**
- LSP spawns in parallel during AST build (warm-up phase)
- Warm-up sends `didOpen` for first Python file found by AST scan
- READY achieved when `publishDiagnostics` received for that specific URI
- Requests ONLY sent when state == READY
- If not READY when needed → fallback to AST-only (no blocking wait)
- No aggressive timeouts: LSP gets full init time (5-10s typical)
- READY is LSP-instance-specific, not global (multiple LSP clients track own state)
