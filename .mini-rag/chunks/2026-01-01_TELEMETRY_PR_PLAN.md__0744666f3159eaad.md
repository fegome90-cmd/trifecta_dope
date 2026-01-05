n = json.loads(last_run_file.read_text())

        latencies = last_run["latencies"]["ctx.search"]

        # Verify percentile ordering: p50 <= p95 <= max
        assert latencies["p50_ms"] <= latencies["p95_ms"]
        assert latencies["p95_ms"] <= latencies["max_ms"]

        # Verify count matches
        assert latencies["count"] == 100
```
