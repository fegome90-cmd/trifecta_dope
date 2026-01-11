### Events in events.jsonl

| Event Type | cmd | Sample Fields | Cardinality |
|---|---|---|---|
| AST parse | `ast.parse` | file, skeleton_bytes, reduction_ratio | Per file |
| AST cache | `ast.cache` | file, cache_hit, prev_sha | Per cache access |
| Selector resolve | `selector.resolve` | symbol_query, resolved, matches | Per symbol lookup |
| LSP spawn | `lsp.spawn` | pyright_binary, subprocess_pid | Per command |
| LSP initialize | `lsp.initialize` | workspace, status | Per spawn |
| LSP ready | `lsp.ready` | ready_via (diagnostics\|definition) | Per spawn, once |
| LSP definition | `lsp.definition` | symbol, resolved, target_file | Per request |
| LSP timeout | `lsp.timeout` | method, timeout_ms, fallback_to | On timeout |
| LSP diagnostics | `lsp.diagnostics` | diag_count, snippet_hash | Per notification |
| File read | `file.read` | file, mode (skeleton\|excerpt\|raw), bytes | Per read |
