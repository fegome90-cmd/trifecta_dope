"publishDiagnostics received"}, "timing_ms": 1500}` |
| `lsp.request` | `method`, `file` (relative), `line`, `col`, `resolved`, `fallback` | `{"cmd": "lsp.request", "args": {"method": "definition", "file": "src/app.py", "line": 42, "col": 10}, "result": {"resolved": true, "target_file": "src/lib.py", "target_line": 15}, "timing_ms": 120, "x": {}}` |
| `lsp.fallback` | `reason`, `fallback_to` | `{"cmd": "lsp.fallback", "args": {"reason": "lsp_not_ready"}, "result": {"fallback_to": "ast_only"}, "timing_ms": 0}` |

### 3. File Read Events

| Event Type | Fields | Example |
|------------|--------|---------|
| `file.read` | `file` (relative), `mode`, `bytes`, `status` | `{"cmd": "file.read", "args": {"file": "src/app.py", "mode": "excerpt"}, "result": {"bytes": 2048, "status": "ok"}, "timing_ms": 5, "x": {"disclosure_mode": "excerpt"}}` |

### 4. Selector Events

| Event Type | Fields | Example |
|------------|--------|---------|
| `selector.resolve` | `symbol_query`, `resolved`, `matches`, `ambiguous` | `{"cmd": "selector.resolve", "args": {"symbol_query": "sym://python/src.domain.models/Config"}, "result": {"resolved": true, "matches": 1, "ambiguous": false}, "timing_ms": 30}` |

---

## Counters (Aggregated in last_run.json)

### AST Counters
- `ast_parse_count`: Total AST parses requested
- `ast_cache_hit_count`: Cache hits (file hash unchanged)
- `ast_cache_miss_count`: Cache m
