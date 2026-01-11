## 🔑 KEY METRICS TO IMPLEMENT

After all 4 tickets are done, you'll be able to query:

```bash
# AST metrics
jq '.ast' _ctx/telemetry/last_run.json
# → {"ast_parse_count": 42, "ast_cache_hit_rate": 0.857}

# LSP metrics
jq '.lsp' _ctx/telemetry/last_run.json
# → {"lsp_spawn_count": 3, "lsp_ready_count": 3, "lsp_timeout_rate": 0.0}

# Bytes by mode
jq '.file_read' _ctx/telemetry/last_run.json
# → {"skeleton_bytes": 8192, "excerpt_bytes": 45678, "raw_bytes": 123456, "total_bytes": 177326}

# LSP definition latencies
jq '.latencies."lsp.definition"' _ctx/telemetry/last_run.json
# → {"count": 5, "p50_ms": 145.0, "p95_ms": 289.0, "max_ms": 512.0}
```

---
