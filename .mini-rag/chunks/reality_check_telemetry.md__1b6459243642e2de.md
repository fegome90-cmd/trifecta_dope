## 🟡 PROBLEMA #4: Schema Pollution

**Telemetry tiene 9 campos top-level**:
```
ts, run_id, segment_id, cmd, args, result, timing_ms, warnings, x
```

**Session necesitaría añadir**:
```
task_type, summary, files_touched, tools_used, outcome, tags
```

**Opciones**:
1. **Top-level** → Rompe el schema estable de telemetry
2. **Bajo `x` namespace** → Session data queda como "extra", no first-class

**Ninguna opción es limpia.**

---
