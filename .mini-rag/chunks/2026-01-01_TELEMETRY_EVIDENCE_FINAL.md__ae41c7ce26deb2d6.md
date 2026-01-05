### Counters in metrics.json (cumulative across all runs)

| Counter | Incremented By | Semantics |
|---|---|---|
| `ast_parse_count` | SkeletonMapBuilder.parse_python() | Total parses |
| `ast_cache_hit_count` | SkeletonMapBuilder cache layer | Cache hits |
| `selector_resolve_count` | Selector.resolve_symbol() | Total resolves |
| `selector_resolve_success_count` | Selector (on success) | Successful resolves |
| `lsp_spawn_count` | LSPClient.__init__() | Processes spawned |
| `lsp_ready_count` | DiagnosticsCollector (on ready) | Ready reached |
| `lsp_timeout_count` | LSPClient.request() (on timeout) | Timeouts |
| `lsp_fallback_count` | LSPClient (on timeout/error) | Fallbacks triggered |
| `file_read_skeleton_bytes_total` | FileSystemAdapter (mode=skeleton) | Bytes read skeleton |
| `file_read_excerpt_bytes_total` | FileSystemAdapter (mode=excerpt) | Bytes read excerpt |
| `file_read_raw_bytes_total` | FileSystemAdapter (mode=raw) | Bytes read raw |
