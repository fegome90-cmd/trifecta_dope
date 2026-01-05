```bash
uv run trifecta session append -s . --summary "Test" --files "a.py"
# Check both destinations:
ls _ctx/session*.md  # Should exist
rg '"cmd": "session.entry"' _ctx/telemetry/events.jsonl | tail -1  # Should show new entry
```

---
