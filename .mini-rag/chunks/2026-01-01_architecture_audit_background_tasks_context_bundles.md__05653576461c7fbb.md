#### 3.3.2 Tests Required

| Test | Assertion | Coverage |
|------|-----------|----------|
| `test_lsp_event_capture_disabled_by_default` | Sin feature flag, LSP events no se capturan | Default behavior |
| `test_lsp_request_logged` | textDocument/definition request se graba | Happy path |
| `test_lsp_timeout_logged_no_crash` | Timeout de LSP → log event, continuar | Resilience |
| `test_lsp_error_logged_no_crash` | Error LSP → log event, continuar | Error handling |
| `test_bundle_with_ast_events_replayable` | Bundle replay puede skip LSP events si no disponible | Replay compatibility |
| `test_ast_events_excluded_from_bundle_if_too_large` | Si AST events > 2MB, solo metadata (no full result) | Bloat protection |
| `test_lsp_server_unavailable_fallback` | Si pyright no instalado → log warning, disable AST capture | Graceful degradation |
| `test_bundle_manifest_includes_lsp_version` | Manifest tiene `lsp_server: "pyright@version"` | Versioning |
