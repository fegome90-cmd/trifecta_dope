### 1. **Duplicación de Sistemas de Logging**

**PROBLEMA**: Ya existe `_ctx/telemetry/events.jsonl`.

| Sistema | Propósito | Overlap? |
|:--------|:----------|:---------|
| `telemetry/events.jsonl` | Comandos ejecutados, tools usados, latencias | ✅ Tools, commands |
| `session_journal.jsonl` (propuesto) | Task type, files touched, tools used | ⚠️ 80% overlap |

**PREGUNTA SIN RESPUESTA**: ¿Por qué necesitamos DOS sistemas? ¿No deberíamos mejorar telemetry en lugar de crear otro silo?

**RIESGO**: Mantenimiento de dos sistemas que hacen casi lo mismo = technical debt.

---
