### T2: LSP Headless Client + On-Demand Execution (4 días)

**Deliverables:**
1. `src/infrastructure/ast_lsp.py`: LSPClient class (JSON-RPC wrapper)
2. `src/infrastructure/ast_lsp.py`: DiagnosticsCollector class
3. `tests/unit/test_lsp_client.py`: 8 unit tests + mock LSP server
4. Timeout + fallback strategy spec

**Definition of Done:**
- [ ] Pyright-langserver subprocess spawned (configurable binary path)
- [ ] JSON-RPC initialization handshake working
- [ ] `textDocument/definition` request sends + parses response
- [ ] `publishDiagnostics` notification collector working (no polling)
- [ ] Timeout 500ms; fallback to Tree-sitter on exceed
- [ ] Process cleanup on exit (kill subprocess, close pipes)
- [ ] 8 unit tests with >80% coverage
- [ ] Mock LSP server in tests (no real pyright in CI)
- [ ] P50 definition request latency <100ms (warm), P95 <200ms

**Tests (Specific):**
```
test_lsp_spawn_pyright_subprocess
test_lsp_json_rpc_initialize_handshake
test_lsp_definition_request_basic
test_lsp_diagnostics_collector_notification
test_lsp_timeout_500ms_exceeds_fallback
test_lsp_process_cleanup_on_exit
test_lsp_cold_start_latency_first_request
test_lsp_fallback_tree_sitter_on_error
```
