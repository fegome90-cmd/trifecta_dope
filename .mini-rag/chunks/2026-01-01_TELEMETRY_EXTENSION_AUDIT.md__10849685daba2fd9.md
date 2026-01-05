### B.1 New Event Types (extend, don't duplicate)

**No new files.** All events go to `events.jsonl` with new `cmd` values:

| Event Type | cmd | Trigger | Fields |
|------------|-----|---------|--------|
| AST skeleton parse | `ast.parse` | SkeletonMapBuilder.parse_python() | file_path_rel, reduction_ratio, skeleton_bytes |
| AST skeleton cache | `ast.cache` | Cache hit/miss | file_path_rel, cache_hit, prev_sha |
| Symbol selector resolve | `selector.resolve` | Selector.resolve_symbol() | symbol_query, resolved, matches_count, ambiguous |
| LSP spawn | `lsp.spawn` | LSPClient.__init__() subprocess spawn | pyright_binary, cold_start_flag |
| LSP initialize | `lsp.initialize` | LSP initialize response received | workspace_initialized, capabilities_received |
| LSP ready | `lsp.ready` | publishDiagnostics OR first hover success | ready_via (diagnostics\|hover), cumulative_ms |
| LSP definition request | `lsp.definition` | textDocument/definition response | symbol_name, resolved, file_path_rel, line_no |
| LSP timeout | `lsp.timeout` | LSP request exceeds 500ms | request_type, timeout_ms, fallback_to |
| LSP diagnostics | `lsp.diagnostics` | publishDiagnostics notification received | first_diag_count, redacted_snippet_hash |
| File read | `file.read` | FileSystemAdapter.read_*() | file_path_rel, read_mode (skeleton\|excerpt\|raw), bytes_read, duration_ms |
