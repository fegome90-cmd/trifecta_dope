#### A) symbol_surface.nl_triggers

```diff
  symbol_surface:
    priority: 2
    nl_triggers:
      - "symbol extraction"
      - "symbol references"
      - "definition lookup"
      - "function implementation"
      - "class initialization"
+     - "telemetry class"
```

**Patch Analysis**:
- **Target FN**: Tasks #17, #35 (Telemetry class/symbol queries)
- **TP Gain**: 0 (blocked by priority 4 "telemetry" single-word)
- **Known Limitation**: Cannot override observability_telemetry.priority=4 single-word triggers
- **Decision**: Kept for documentation; future priority adjustment could enable
