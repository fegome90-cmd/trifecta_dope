### 4.2 `events.jsonl` (Telemetry Extended for Bundles)

Cada línea es un JSON con el formato:

```json
{
  "ts": "2026-01-01T12:00:01.123Z",
  "run_id": "run_1735772400",
  "segment": "trifecta_dope",
  "cmd": "ctx.search",
  "args": {"query": "validate segment", "limit": 5},
  "result": {"status": "ok", "hits": 3},
  "timing_ms": 45,
  "warnings": [],
  "tool_call_id": "tc_001",
  "parent_trace_id": null,
  "execution_order": 1
}
```

**Nuevos Campos para Bundles**:
- `tool_call_id`: UUID único del tool call (para grafos de dependencia).
- `parent_trace_id`: ID del tool call padre (para nested calls).
- `execution_order`: Orden secuencial (para replay determinista).

---
