### Generate Telemetry Events
```bash
# Run demo and check telemetry output
PYTHONPATH=/workspaces/trifecta_dope python scripts/demo_pr2.py

# Inspect generated events
cat _ctx/telemetry/events.jsonl | tail -5

# Inspect metrics
cat _ctx/telemetry/last_run.json | jq '.ast, .lsp, .file_read, .telemetry_drops'
```

---
