### B.3 Metrics Counter Extensions

**Existing counters (metrics.json):**
- `ctx_build_count`, `ctx_search_count`, `ctx_get_count`, etc.

**New counters (via `telemetry.incr()`):**
| Counter | Semantics | Incremented Where |
|---------|-----------|-------------------|
| `ast_parse_count` | Total skeleton parses | SkeletonMapBuilder.parse_python() |
| `ast_cache_hit_count` | Cache hits | SkeletonMapBuilder (cache layer) |
| `selector_resolve_count` | Symbol resolutions attempted | Selector.resolve_symbol() |
| `selector_resolve_success_count` | Resolutions succeeded | Selector.resolve_symbol() (on success) |
| `lsp_spawn_count` | LSP processes spawned | LSPClient.__init__() |
| `lsp_ready_count` | LSP reached ready state | DiagnosticsCollector._on_ready() |
| `lsp_timeout_count` | LSP requests timed out | LSPClient.request() on timeout |
| `lsp_fallback_count` | Fallback to Tree-sitter triggered | LSPClient.request() (on timeout or error) |
| `file_read_skeleton_bytes_total` | Total bytes via skeleton mode | FileSystemAdapter.read_*(..., mode="skeleton") |
| `file_read_excerpt_bytes_total` | Total bytes via excerpt mode | FileSystemAdapter.read_*(..., mode="excerpt") |
| `file_read_raw_bytes_total` | Total bytes via raw mode | FileSystemAdapter.read_*(..., mode="raw") |
