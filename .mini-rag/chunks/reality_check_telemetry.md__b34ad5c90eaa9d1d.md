## 🟢 LA ÚNICA FORMA EN QUE FUNCIONA

**Opción Híbrida**:
1. Telemetry sigue siendo telemetry (no cambios)
2. NUEVO evento tipo `session.entry` que SE REGISTRA en telemetry JSONL
3. Session.md se genera DESDE filtrar `cmd == "session.entry"` del telemetry JSONL

**Schema**:
```json
{
  "ts": "2026-01-04T09:50:21-03:00",
  "run_id": "run_X",
  "segment_id": "abc123",
  "cmd": "session.entry",
  "args": {"summary": "Fixed bug", "files": ["a.py"], "type": "debug"},
  "result": {"outcome": "success"},
  "timing_ms": 0,
  "warnings": [],
  "x": {"tags": ["lsp", "daemon"]}
}
```

**VENTAJAS**:
- ✅ Un solo archivo JSONL (telemetry)
- ✅ Session entries son events más de telemetry
- ✅ Telemetry schema no se contamina (es solo otro `cmd`)

**DESVENTAJAS**:
- ⚠️ Session entries mezcladas con ruido de lsp.spawn, ctx.sync, etc.
- ⚠️ Query `session.entry` requiere filtrar TODO el JSONL
- ⚠️ Telemetry crece más rápido (session + metrics)

---
