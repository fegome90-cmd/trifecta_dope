#### File: `src/infrastructure/telemetry.py`

**Line 113: Modify `event()` signature**
```python
def event(
    self,
    cmd: str,
    args: Dict[str, Any],
    result: Dict[str, Any],
    timing_ms: int,
    warnings: List[str] | None = None,
    **extra_fields: Any,  # NEW: accept arbitrary kwargs
) -> None:
    """
    Log a discrete event with optional structured fields.

    Extra fields will be serialized directly to the event JSON.
    Example: telemetry.event("ctx.search", {...}, {...}, 100, bytes_read=1024)
    """
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
        **extra_fields,  # NEW: merge all extra fields into payload
    }

    try:
        self._write_jsonl("events.jsonl", payload)
        if timing_ms > 0:
            self.observe(cmd, timing_ms)
        # ... rest of token tracking unchanged ...
```

**Line 245: Add AST/LSP/file_read summaries to `flush()`**
