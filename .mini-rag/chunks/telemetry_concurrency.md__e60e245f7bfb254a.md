## Drop Tracking (PR#1)

The telemetry system tracks its own losses:

```python
# In TelemetryTracker
self.telemetry_events_attempted = 0  # Total events attempted
self.telemetry_lock_skipped = 0       # Drops due to lock contention

def event(self, cmd, args, result, timing_ms, warnings=None, **extra_fields):
    self.telemetry_events_attempted += 1
    success = self._write_jsonl("events.jsonl", payload)
    if not success:
        self.telemetry_lock_skipped += 1
```

**Summary in `last_run.json`:**
```json
{
  "telemetry_drops": {
    "lock_skipped": 3,
    "attempted": 100,
    "written": 97,
    "drop_rate": 0.03
  }
}
```

**Interpretation:**
- `lock_skipped`: Events dropped due to lock contention
- `attempted`: Total event writes attempted
- `written`: Successfully written events (`attempted - lock_skipped`)
- `drop_rate`: Ratio of drops (`lock_skipped / attempted`)

---
