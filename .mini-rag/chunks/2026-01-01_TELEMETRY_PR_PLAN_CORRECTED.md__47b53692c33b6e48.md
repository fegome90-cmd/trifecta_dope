#### File: `src/infrastructure/ast_lsp.py` (NEW)

**Implementation highlights:**
- Tree-sitter Python parser integration
- Skeleton map extraction (functions, classes, imports only)
- Content-based caching (SHA-256 hash)
- All paths use `_relpath()` from PR#1
- All timings use `perf_counter_ns()`
- Emit `ast.parse` events with telemetry
