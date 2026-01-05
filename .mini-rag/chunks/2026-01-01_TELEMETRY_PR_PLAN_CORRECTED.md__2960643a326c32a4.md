#### Definition of Done (Ticket 2.2)

- [ ] LSP integration gated behind `LSP_ENABLED=true` env var (experimental)
- [ ] LSP implementation choice documented: pyright (requires Node.js) vs basedpyright (pure Python)
- [ ] Chosen LSP binary subprocess spawned successfully (pyright-langserver or basedpyright-langserver)
- [ ] JSON-RPC Content-Length framing implemented
- [ ] State machine (COLD/WARMING/READY/FAILED) implemented
- [ ] `initialize` request sent and `InitializeResult` parsed
- [ ] Warm-up sends `didOpen` for 1 file to trigger diagnostics
- [ ] First `publishDiagnostics` notification triggers READY state
- [ ] Requests ONLY sent when state == READY
- [ ] Fallback to AST-only if not READY
- [ ] All file paths logged as relative
- [ ] No aggressive timeouts (5-10s init time allowed)
- [ ] Unit test: `test_lsp_state_transitions` (COLD→WARMING→READY)
- [ ] Unit test: `test_lsp_ready_gating` (no requests before READY)
- [ ] Unit test: `test_lsp_fallback` (AST-only when not READY)
- [ ] Integration test: full lifecycle (spawn→init→didOpen→diagnostics→READY→request) - skippable if pyright not available
- [ ] Mypy clean

---
