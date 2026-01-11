## Verification

Check for PII in telemetry:

```bash
# Search for common PII patterns
rg "/Users/|/home/|/private/var/|file://|C:\\Users\\" ./_ctx/telemetry/events.jsonl

# If output is empty, telemetry is clean
```

---
