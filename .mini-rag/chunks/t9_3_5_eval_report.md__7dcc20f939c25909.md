#### Task #35: "symbols in the telemetry module and their relationships"

| Version | Got | selected_by | Status |
|---------|-----|-------------|--------|
| Before | observability_telemetry | nl_trigger | ❌ Wrong |
| After | fallback | fallback | ❌ Regression |

**Why**: Single-word telemetry trigger is clamped; no higher-specificity match exists in current nl_triggers.

---
