### A.3 Aggregation Format (last_run.json)

**Example from last_run.json (truncated):**
```json
{
  "run_id": "run_1767232876",
  "ts": "2026-01-01T02:01:16.990404+00:00",
  "metrics_delta": {
    "ctx_stats_count": 1
  },
  "latencies": {
    "ctx.stats": {
      "count": 1,
      "p50_ms": 7.0,
      "p95_ms": 7.0,
      "max_ms": 7.0
    }
  },
  "tokens": {},
  "top_warnings": [],
  "pack_state": {
    "pack_sha": "365c67055285ad84",
    "pack_mtime": 1767230435.5603714
  }
}
```

**Key observations:**
- `latencies[cmd]` includes: count, p50_ms, p95_ms, max_ms (calculated in `flush()` line 231-242)
- Percentiles calculated on-the-fly from in-memory `self.latencies[cmd]` array (stored in **microseconds**, converted to ms in output)
- `pack_sha` is 16-char hash of context_pack.json (for stale detection)
- `pack_mtime` is float (Unix seconds) for mtime tracking
