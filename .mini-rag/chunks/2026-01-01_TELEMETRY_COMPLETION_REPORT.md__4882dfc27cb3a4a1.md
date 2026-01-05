## METRICS YOU'LL BE ABLE TO MEASURE

After implementation, query with:

```bash
# 1. AST PERFORMANCE
jq '.ast' _ctx/telemetry/last_run.json
# {
#   "ast_parse_count": 42,
#   "ast_cache_hit_count": 36,
#   "ast_cache_hit_rate": 0.857
# }

# 2. LSP LIFECYCLE
jq '.lsp' _ctx/telemetry/last_run.json
# {
#   "lsp_spawn_count": 3,
#   "lsp_ready_count": 3,
#   "lsp_timeout_count": 0,
#   "lsp_fallback_count": 0,
#   "lsp_timeout_rate": 0.0
# }

# 3. BYTES READ BY MODE
jq '.file_read' _ctx/telemetry/last_run.json
# {
#   "skeleton_bytes": 8192,
#   "excerpt_bytes": 45678,
#   "raw_bytes": 123456,
#   "total_bytes": 177326
# }

# 4. LATENCIES (p50/p95/max)
jq '.latencies."lsp.definition"' _ctx/telemetry/last_run.json
# {
#   "count": 5,
#   "p50_ms": 145.0,
#   "p95_ms": 289.0,
#   "max_ms": 512.0
# }

# 5. ALL AST PARSE EVENTS
jq 'select(.cmd == "ast.parse")' _ctx/telemetry/events.jsonl
```

---
