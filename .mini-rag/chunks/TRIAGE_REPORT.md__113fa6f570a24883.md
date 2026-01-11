### Fix 2: Telemetry reserved key protection (14 failures)

Agregar validación en `event()`:
```python
RESERVED_KEYS = {"ts", "run_id", "segment_id", "cmd", "args", "result", "timing_ms", "warnings", "x"}
collisions = set(kwargs.keys()) & RESERVED_KEYS
if collisions:
    raise ValueError(f"Cannot use reserved keys: {collisions}")
```
