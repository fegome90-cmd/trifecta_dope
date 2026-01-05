## SUCCESS METRICS (Post-Deployment)

After both PRs merged, these queries should work:

```bash
# Query AST metrics
jq '.ast' _ctx/telemetry/last_run.json
# Output: {"ast_parse_count": 42, "ast_cache_hit_count": 36, "ast_cache_hit_rate": 0.857}

# Query LSP metrics
jq '.lsp' _ctx/telemetry/last_run.json
# Output: {"lsp_spawn_count": 3, "lsp_ready_count": 3, "lsp_ready_rate": 1.0, ...}

# Query bytes by mode
jq '.file_read' _ctx/telemetry/last_run.json
# Output: {"skeleton_bytes": 8192, "excerpt_bytes": 45678, "raw_bytes": 123456, ...}

# Query LSP definition latencies
jq '.latencies."lsp.request"' _ctx/telemetry/last_run.json
# Output: {"count": 5, "p50_ms": 145.0, "p95_ms": 289.0, "max_ms": 512.0}

# Query drop rate (lossy fcntl)
jq '.telemetry_drops' _ctx/telemetry/last_run.json
# Output: {"lock_skipped": 3, "drop_rate": 0.0067}  # 0.67% < 2% threshold ✅
```

---
