```python
def test_ast_event_uses_monotonic_clock(tmp_path):
    """Verify AST events use perf_counter_ns, not time.time()."""
    import json
    telemetry = Telemetry(tmp_path, level="lite")

    # Parse with instrumentation
    start_ns = time.perf_counter_ns()
    time.sleep(0.01)  # 10ms
    elapsed_ms = int((time.perf_counter_ns() - start_ns) / 1_000_000)

    telemetry.event(
        "ast.parse",
        {"file": "test.py"},
        {"status": "ok"},
        elapsed_ms,
    )
    telemetry.flush()

    # Read back event
    events_file = tmp_path / "_ctx" / "telemetry" / "events.jsonl"
    assert events_file.exists()

    with open(events_file) as f:
        event = json.loads(f.readline())

    # Assert timing is reasonable (10-20ms for the 10ms sleep + overhead)
    assert 8 <= event["timing_ms"] <= 30, f"Timing {event['timing_ms']}ms is unrealistic"
```
