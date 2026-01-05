ra_fields contains reserved keys: {collision}. "
            f"Reserved: {RESERVED_KEYS}"
        )

    safe_args = self._sanitize_args(args)
    tokens = self._estimate_token_usage(cmd, args, result)

    # NEW: compute stable segment_id (no path leakage)
    import hashlib
    segment_id = hashlib.sha256(str(self.segment_path).encode()).hexdigest()[:8]

    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "run_id": self.run_id,
        "segment_id": segment_id,  # FIX: stable ID, no absolute path
        "cmd": cmd,
        "args": safe_args,
        "result": result,
        "timing_ms": timing_ms,
        "tokens": tokens,
        "warnings": warnings or [],
        "x": extra_fields,  # NEW: namespace extra fields to prevent future collisions
    }

    # NEW: _write_jsonl now returns success bool for drop tracking
    if self._write_jsonl("events.jsonl", payload):
        if timing_ms > 0:
            self.observe(cmd, timing_ms)
        # (rest of token tracking unchanged)
    else:
        # Lock not acquired: track drop
        self.incr("telemetry_lock_skipped", 1)
```
