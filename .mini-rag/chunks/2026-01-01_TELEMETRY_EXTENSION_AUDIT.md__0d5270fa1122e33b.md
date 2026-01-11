### E.3 Synthetic Dataset for Summary Validation

**File:** `tests/fixtures/synthetic_telemetry.py` (NEW)

```python
def generate_synthetic_events(n_events: int) -> list[dict]:
    """Generate synthetic events for summary calculation validation."""
    events = []
    for i in range(n_events):
        events.append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "run_id": f"run_{i}",
            "cmd": "ctx.search",
            "args": {"query": f"test{i}"},
            "result": {"hits": i % 10},
            "timing_ms": 10 + i % 100,  # 10–110ms range
        })
    return events

def test_summary_p50_p95_calculation():
    """Verify percentile math with synthetic data."""
    events = generate_synthetic_events(100)
    times = [e["timing_ms"] for e in events]
    times_sorted = sorted(times)

    p50_expected = times_sorted[50]  # Median
    p95_expected = times_sorted[int(100 * 0.95)]

    # ... call Telemetry.flush() and parse last_run.json ...

    assert last_run["latencies"]["ctx.search"]["p50_ms"] == p50_expected
    assert last_run["latencies"]["ctx.search"]["p95_ms"] == p95_expected
```

---
