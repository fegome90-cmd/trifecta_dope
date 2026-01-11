### Option 2: Scrub (Preserve History)

```bash
python scripts/scrub_telemetry_pii.py ./_ctx/telemetry/events.jsonl
```

This rewrites the file with PII patterns replaced by `<ABS_PATH_REDACTED>`.

**Backup**: The scrubber creates a `.bak` backup before modifying the file.

---
