### 3. LSP On-Demand (No Daemon in v0)

**Architecture:**

```
CLI invocation (ctx search ...)
    ↓
ContextService.search()
    ↓
Try LSP (if timeout < 500ms) → Fallback Tree-sitter instant
    ├─ Spawn pyright-langserver process
    ├─ Send JSON-RPC textDocument/definition request
    ├─ Await response (timeout 500ms)
    ├─ Parse diagnostics from notificationspublishDiagnostics
    └─ Kill process
    ↓
Return results
```

**Requests Implemented (MVP):**
- `textDocument/definition`: Resolve symbol → file:line
- `textDocument/diagnostics`: Collect errors via `publishDiagnostics` notification

**NOT Implemented (Phase 2):**
- `textDocument/references`
- `textDocument/hover`
- `textDocument/documentSymbol` (Tree-sitter already covers this)

**Diagnostics Collector:**
