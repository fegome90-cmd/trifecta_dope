### Test Cases

| Task | Single-Words Detected | Guardrail Result | Expected |
|------|----------------------|------------------|----------|
| "telemetry" | ["telemetry"] (obs, priority=4) | ✅ Allowed | obs_telemetry |
| "architecture" | ["architecture"] (arch, priority=2) | ✅ Blocked (priority < 4) | fallback |
| "telemetry architecture overview" | ["telemetry"] (obs, priority=4), ["architecture"] (arch, priority=2) | ✅ Blocked (conflict + arch priority < 4) | fallback |

**Result**: Guardrail working correctly — prevents single-word overmatching while allowing high-priority single-words.

---
