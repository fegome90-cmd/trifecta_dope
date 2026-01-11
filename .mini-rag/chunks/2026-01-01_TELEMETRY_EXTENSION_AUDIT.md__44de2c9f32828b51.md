### A.1 Telemetry Architecture (As-Is)

**Sink Location:** `_ctx/telemetry/` (within segment directory)

```
_ctx/telemetry/
├── events.jsonl          # Append-only log of discrete events (rotated at 5MB)
├── events.1.jsonl        # Rotation backup (if >5MB)
├── events.2.jsonl        # Older backup
├── metrics.json          # Cumulative counters (aggregated across all runs)
└── last_run.json         # Summary of last execution (latencies, tokens, pack_state)
```

**Class:** `src/infrastructure/telemetry.py` line 16: `class Telemetry`

**Key Methods:**
| Method | Purpose | Called From | Evidence |
|--------|---------|-------------|----------|
| `__init__(segment_path, level, run_id)` | Initialize telemetry, create dirs | cli.py:51 `_get_telemetry()` | ✅ CONFIRMED |
| `event(cmd, args, result, timing_ms, warnings)` | Log discrete event to events.jsonl | cli.py:182+ (search, get, validate, etc.) | ✅ CONFIRMED |
| `observe(cmd, ms)` | Record latency in microseconds | cli.py:279 (ctx.search), 317 (ctx.get), 351 (ctx.validate) | ✅ CONFIRMED |
| `incr(name, n=1)` | Increment counter in memory | Used by use_cases (not yet in CLI commands) | ⏳ SPARSE |
| `flush()` | Persist metrics.json + last_run.json | cli.py:188, 203, 220, etc. | ✅ CONFIRMED |
