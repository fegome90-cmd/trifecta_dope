### Test Strategy (PR#1)

```python
def test_concurrent_writes_no_corruption(tmp_path):
    """
    50 processes × 20 events = 1000 total writes.
    - MUST: No corrupted lines, all valid JSON
    - MUST NOT: Exact 1000 events (lossy drops OK)
    """
    import multiprocessing

    def worker(tracker, proc_id):
        for i in range(20):
            tracker.event(f"test.{proc_id}", {"i": i}, {"ok": True}, timing_ms=1)

    processes = [
        multiprocessing.Process(target=worker, args=(tracker, i))
        for i in range(50)
    ]
    for p in processes: p.start()
    for p in processes: p.join()

    # Verify: no corrupted lines
    with open(events_file) as f:
        for line in f:
            json.loads(line)  # Raises if corrupted

    # Accept: drop_rate < 0.05 (5%)
    assert tracker.telemetry_lock_skipped / 1000 < 0.05
```
