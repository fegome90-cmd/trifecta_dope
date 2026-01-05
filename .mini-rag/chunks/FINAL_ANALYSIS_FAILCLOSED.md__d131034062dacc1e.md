```python
# V1 debe hacer dual write:
# 1. Write to telemetry (new)
telemetry.event(cmd="session.entry", args={...}, result={...}, timing_ms=0)

# 2. Write to session.md (existing - keep for backward compat)
with open(session_file, "a") as f:
    f.write(entry_text)
```

---
