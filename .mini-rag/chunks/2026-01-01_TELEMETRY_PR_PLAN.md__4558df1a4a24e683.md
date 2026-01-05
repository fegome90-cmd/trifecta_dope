_path):
        """Verify percentile math on synthetic data."""
        telemetry = Telemetry(tmp_path, level="lite")

        # Record 100 latency observations
        times_ms = [10 + (i % 100) for i in range(100)]
        for t in times_ms:
            telemetry.observe("test.cmd", t)

        telemetry.flush()

        last_run_file = tmp_path / "_ctx" / "telemetry" / "last_run.json"
        last_run = json.loads(last_run_file.read_text())

        # Verify counts and percentiles are in expected range
        assert last_run["latencies"]["test.cmd"]["count"] == 100
        assert 10 <= last_run["latencies"]["test.cmd"]["p50_ms"] <= 60
        assert 10 <= last_run["latencies"]["test.cmd"]["p95_ms"] <= 110
```
