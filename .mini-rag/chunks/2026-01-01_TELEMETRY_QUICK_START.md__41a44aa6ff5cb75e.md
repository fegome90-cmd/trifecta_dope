## EXAMPLE: First Event You'll Emit

After implementing Ticket 1 + 2:

```json
{
  "ts": "2026-01-01T12:34:56.789012+00:00",
  "run_id": "run_1767123456",
  "segment": "/workspaces/trifecta_dope",
  "cmd": "ast.parse",
  "args": {"file": "src/domain/models.py"},
  "result": {"functions": 12, "classes": 3, "status": "ok"},
  "timing_ms": 42,
  "tokens": {...},
  "warnings": [],
  "skeleton_bytes": 8192,
  "reduction_ratio": 0.0234
}
```

And in last_run.json:

```json
{
  "run_id": "run_1767123456",
  "latencies": {
    "ast.parse": {
      "count": 15,
      "p50_ms": 38.0,
      "p95_ms": 52.0,
      "max_ms": 73.0
    }
  },
  "ast": {
    "ast_parse_count": 15,
    "ast_cache_hit_count": 11,
    "ast_cache_hit_rate": 0.733
  }
}
```

---
