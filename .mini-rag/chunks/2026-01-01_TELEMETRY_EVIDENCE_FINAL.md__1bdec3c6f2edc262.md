#### Aggregation Format (Actual)
**Sample from last_run.json:**
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

**Aggregation fields:** run_id, ts, metrics_delta, latencies, tokens, top_warnings, pack_state ✅
