### 📍 Ronda 4: Vector de Duplicación con Telemetry (ACTUALIZADO)
**Timestamp**: 11:13
**Vector Aplicado**: Hidden Assumptions

**Red Team ataca**:
```
OVERLAP CON TELEMETRY (refinado con clarificaciones):

TELEMETRY ACTUAL (`_ctx/telemetry/events.jsonl`):
- ts, run_id, segment_id
- cmd (ej: "ctx.sync", "ctx.search", "session.append")
- args, result, timing_ms
- x namespace para extras

SESSION JSONL PROPUESTO (`_ctx/session_journal.jsonl`):
- timestamp
- task_type (debug/develop/document)
- summary
- files_touched (manual via --files)
- commands_executed (manual via --commands)
- outcome, tags

PREGUNTA DE ARQUITECTURA:
¿Por qué NO usar telemetry con un event type `session.entry`?

OPCIÓN HÍBRIDA:
```json
{
  "ts": "2026-01-04T11:00:00",
  "cmd": "session.entry",
  "args": {
    "summary": "Fixed bug",
    "type": "debug",
    "files": ["a.py"],
    "commands": ["pytest"]
  },
  "result": {"outcome": "success"},
  "x": {"tags": ["lsp", "daemon"]}
}
```

VENTAJAS:
- ✅ Un solo JSONL (telemetry)
- ✅ Reutiliza infraestructura existente
- ✅ Session entries son events más del sistema

DESVENTAJAS:
- ⚠️ Session mezclado con ruido (lsp.spawn, ctx.sync, etc.)
- ⚠️ Query requiere filtrar TODO telemetry JSONL

PREGUNTA: ¿Dos JSONL separados es realmente mejor que event type en telemetry?
Justifica con métricas de query performance o admite que es preferencia estética.
```
