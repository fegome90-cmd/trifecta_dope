### C.2 Telemetry Module Changes

**File:** `src/infrastructure/telemetry.py`

**Modifications:**
1. [ ] Line 113: Extend `event()` signature to accept `**extra_fields`
2. [ ] Line 145: Merge `extra_fields` into `payload` dict before write
3. [ ] Add comment documenting new AST/LSP event types
4. [ ] No changes to `observe()`, `incr()`, `flush()` (backward compatible)

**Code diff (minimal):**
```python
def event(
    self,
    cmd: str,
    args: Dict[str, Any],
    result: Dict[str, Any],
    timing_ms: int,
    warnings: List[str] | None = None,
    **extra_fields,  # NEW
) -> None:
    """Log a discrete event with optional extended fields."""
    if not self.enabled:
        return

    if warnings:
        self.warnings.extend(warnings)

    safe_args = self._sanitize_args(args)
    tokens = self._estimate_token_usage(cmd, args, result)

    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "run_id": self.run_id,
        "segment": str(self.segment_path),
        "cmd": cmd,
        "args": safe_args,
        "result": result,
        "timing_ms": timing_ms,
        "tokens": tokens,
        "warnings": warnings or [],
        **extra_fields,  # NEW: merge arbitrary fields
    }

    # ... rest of event() unchanged ...
```
