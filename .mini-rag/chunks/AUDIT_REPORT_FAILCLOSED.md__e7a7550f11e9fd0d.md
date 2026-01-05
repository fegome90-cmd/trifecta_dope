#### Step 5: Audit Privacy (Blocker #6, #7)

**5a) Inspect _sanitize_event**:
```bash
rg "def _sanitize_event" src/infrastructure/telemetry.py -A 30
```

**Expected**: Function should redact absolute paths in `args`

**If NOT**: Add sanitization:
```python
def _sanitize_event(event: dict) -> dict:
    """Sanitize PII from event before writing."""
    # Existing logic...

    # NEW: Sanitize session.entry args
    if event["cmd"] == "session.entry":
        if "files" in event["args"]:
            event["args"]["files"] = [
                _relpath(f) for f in event["args"]["files"]
            ]

    return event
```

**5b) Run privacy test**:
```bash
pytest tests/acceptance/test_no_privacy_leaks.py -v
# MUST pass
```

---
