```
┌─────────────────────────────────────────────────┐
│  CLI Commands (search, get, validate, stats)    │
│  src/infrastructure/cli.py                      │
└──────────────────┬──────────────────────────────┘
                   │ calls
                   ↓
    ┌──────────────────────────┐
    │   Telemetry API          │
    │  (event, observe, incr)  │
    │  src/infrastructure/     │
    │    telemetry.py          │
    └──────────────┬───────────┘
                   │
      ┌────────────┴────────────┐
      │                         │
      ↓                         ↓
┌──────────────┐        ┌─────────────────┐
│  events.json │        │  metrics.json   │
│  (JSONL log) │        │  (counters)     │
│  append-only │        │  aggregated     │
│  rotated     │        │  per-run        │
└──────────────┘        └────────┬────────┘
                                 │
                                 ↓
                        ┌─────────────────┐
                        │ last_run.json   │
                        │ (summary)       │
                        │ p50/p95/max     │
                        │ latencies       │
                        └─────────────────┘

NEW (AST/LSP) LAYER:
┌─────────────────────────────────────────────────┐
│  AST (SkeletonMapBuilder) + LSP (LSPClient)     │
│  + Selector + Instrumentation                   │
│  src/infrastructure/ast_lsp.py (NEW)
