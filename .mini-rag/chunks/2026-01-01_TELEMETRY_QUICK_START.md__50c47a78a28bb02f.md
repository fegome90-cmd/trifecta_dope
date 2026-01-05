### Key Deliverables
| Metric | Where | How to Query |
|--------|-------|--------------|
| **AST parse latency** | events.jsonl | `jq 'select(.cmd=="ast.parse") | .timing_ms'` |
| **LSP ready time** | last_run.json | `jq '.latencies."lsp.ready".p50_ms'` |
| **Bytes read by mode** | last_run.json | `jq '.file_read'` → skeleton/excerpt/raw totals |
| **Fallback rate** | last_run.json | `jq '.lsp.lsp_timeout_rate'` |
| **Cache hit rate** | last_run.json | `jq '.ast.ast_cache_hit_rate'` |
