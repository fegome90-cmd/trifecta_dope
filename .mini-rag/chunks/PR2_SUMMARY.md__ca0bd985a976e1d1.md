### ✅ LSP (Hito 4 - Completed, EXPERIMENTAL)
- [x] LSPManager with state machine (COLD→WARMING→READY→FAILED)
- [x] Warm-up policy: non-blocking spawn after AST localizes candidate
- [x] READY-only gating: definition/hover only if state==READY
- [x] JSON-RPC framing (Content-Length header)
- [x] Telemetry: lsp.spawn, lsp.state_change, lsp.request, lsp.fallback
- [x] Counters: lsp_spawn_count, lsp_ready_count, lsp_failed_count, lsp_fallback_count
- [x] Tests: 8 tests for state machine + READY-only gating
