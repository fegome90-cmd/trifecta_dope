### 1. Schema Version Update (v2 → v3)

**File**: `_ctx/aliases.yaml`

```yaml
# Header
schema_version: 3  # Added nl_triggers[] for direct L2 matching

# Feature structure
observability_telemetry:
  priority: 4
  nl_triggers:  # NEW
    - "ctx stats"
    - "telemetry statistics"
    - "search performance"
    - "token tracking"
    - "event tracking"
  triggers:  # Existing (now L3)
    - phrase: "ctx stats"
      terms: ["ctx", "stats"]
      high_signal: true
      notes: "CLI command for telemetry statistics"
```
