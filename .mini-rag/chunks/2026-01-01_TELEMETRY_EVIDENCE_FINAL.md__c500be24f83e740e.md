tation                   │
│  src/infrastructure/ast_lsp.py (NEW)            │
└──────────────────┬──────────────────────────────┘
                   │ calls
                   ↓ telemetry.event() with:
        - perf_counter_ns() for timing
        - relative paths (no absolute)
        - new fields: bytes_read, cache_hit, fallback_to
        - counters: ast_parse_count, lsp_spawn_count, etc.
                   │
      ┌────────────┴────────────┐
      ↓                         ↓
  Same sinks             Extended summaries
  (events.jsonl +        (ast, lsp, file_read
   metrics.json)         in last_run.json)
```
