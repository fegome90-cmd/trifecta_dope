### Bucket 2: Telemetry Reserved Keys (14 failures)

```
tests/unit/test_telemetry_extension.py:20: Failed: DID NOT RAISE <class 'ValueError'>
```

**Tests esperan**:
```python
with pytest.raises(ValueError, match="reserved keys"):
    telemetry.event("test", {}, {}, 100, ts="2026-01-01")  # ts is reserved
```

**Fix**: Agregar validación en `Telemetry.event()` para reserved keys.

**ROI**: 14 failures → 0 failures

---
