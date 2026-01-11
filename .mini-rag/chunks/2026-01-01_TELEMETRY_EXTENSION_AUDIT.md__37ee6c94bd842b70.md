### B.2 Extended Fields in Existing Events

**Modify `event()` signature to accept optional structured fields:**

```python
def event(
    self,
    cmd: str,
    args: Dict[str, Any],
    result: Dict[str, Any],
    timing_ms: int,
    warnings: List[str] | None = None,
    **extra_fields  # NEW: accept arbitrary kwargs for extensibility
) -> None:
```

**Usage example:**
```python
telemetry.event(
    "ctx.search",
    {"query": "context routing"},
    {"hits": 2, "returned_ids": [...]},
    timing_ms=145,
    bytes_read=8192,              # NEW
    disclosure_mode="excerpt",    # NEW
    cache_hit_rate=0.87           # NEW
)
```

**Payload becomes:**
```json
{
  "ts": "2025-12-30...",
  "run_id": "run_...",
  "cmd": "ctx.search",
  "args": {"query": "context routing"},
  "result": {"hits": 2, ...},
  "timing_ms": 145,
  "bytes_read": 8192,             # ← NEW FIELD
  "disclosure_mode": "excerpt",   # ← NEW FIELD
  "cache_hit_rate": 0.87          # ← NEW FIELD
}
```
