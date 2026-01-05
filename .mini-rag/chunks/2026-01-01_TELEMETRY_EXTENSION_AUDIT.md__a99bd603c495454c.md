## SUCCESS METRICS (Post-Implementation)

Once implemented, you should be able to run:

```bash
# Query last_run.json for AST metrics
cat _ctx/telemetry/last_run.json | jq '.ast'
# Output:
# {
#   "ast_parse_count": 42,
#   "ast_cache_hit_rate": 0.86
# }

# Query for LSP metrics
cat _ctx/telemetry/last_run.json | jq '.lsp'
# Output:
# {
#   "lsp_spawn_count": 3,
#   "lsp_ready_count": 3,
#   "lsp_timeout_count": 0,
#   "lsp_timeout_rate": 0.0,
#   "lsp_fallback_count": 0
# }

# Query for bytes by mode
cat _ctx/telemetry/last_run.json | jq '.file_read'
# Output:
# {
#   "skeleton_bytes": 8192,
#   "excerpt_bytes": 45678,
#   "raw_bytes": 123456,
#   "total_bytes": 177326
# }

# Query latencies
cat _ctx/telemetry/last_run.json | jq '.latencies."lsp.definition"'
# Output:
# {
#   "count": 5,
#   "p50_ms": 145.0,
#   "p95_ms": 289.0,
#   "max_ms": 512.0
# }
```

---

**Audit Complete:** 2026-01-01  
**Next Step:** Begin Day 1 implementation  
**Owner:** Senior Engineer / Telemetry Architect
