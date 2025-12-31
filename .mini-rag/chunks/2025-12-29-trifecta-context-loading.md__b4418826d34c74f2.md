## Autopilot: Automated Context Refresh

A background watcher (not the LLM) ensures the Context Pack stays fresh. Configuration in `session.md`:

```yaml
autopilot:
  enabled: true
  debounce_ms: 5000
  steps: ["trifecta ctx build", "trifecta ctx validate"]
  timeouts: {"build": 30, "validate": 5}
```

---
