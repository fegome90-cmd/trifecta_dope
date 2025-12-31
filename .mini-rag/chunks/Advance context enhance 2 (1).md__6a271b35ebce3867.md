## Autopilot: Automated Context Refresh

In `session.md`, embed a YAML block for machine-readable configuration:

```yaml
---
autopilot:
  enabled: true
  debounce_ms: 5000
  steps:
    - command: trifecta ctx build
      timeout_ms: 30000
    - command: trifecta ctx validate
      timeout_ms: 5000
  max_rounds_per_turn: 2
---
```

A watcher (not the LLM) runs in the background:

1. Detects file changes
2. Debounces
3. Runs `ctx build`
4. Runs `ctx validate`
5. Logs to `_ctx/autopilot.log`

This keeps context fresh without manual intervention.
