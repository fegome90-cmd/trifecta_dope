#### B) observability_telemetry.nl_triggers
```diff
  observability_telemetry:
    priority: 4
    nl_triggers:
      - "ctx stats"
      - "telemetry statistics"
      - "search performance"
      - "token tracking"
      - "event tracking"
+     - "telemetry"    # NEW (single-word)
+     - "metrics"       # NEW (single-word)
+     - "events.jsonl"  # NEW (single-word)
```
