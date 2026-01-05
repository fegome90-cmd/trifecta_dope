## El Schema Actual de Telemetry

```json
{
  "ts": "2026-01-01T19:17:00-0300",
  "run_id": "run_1767305820",
  "segment_id": "6f25e381",
  "cmd": "lsp.spawn",
  "args": {"executable": "pylsp"},
  "result": {"status": "ok", "pid": 16994},
  "timing_ms": 1,
  "warnings": [],
  "x": {"lsp_state": "WARMING"}
}
```

**Granularidad**: Evento por COMANDO (ctx.search, lsp.spawn, ast.parse)  
**Propósito**: Observability - latencias, errores, métricas de performance

---
