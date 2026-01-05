# Mantener JSONL activo < 10K eventos
```

¿Implementarás telemetry rotation o tolerarás queries lentas?

---

### Problema #2: Schema Pollution
**REALIDAD**:
Telemetry schema está OPTIMIZADO para observability:
- `timing_ms`: Crítico para latencias
- `warnings`: Crítico para errores
- `result.status`: Crítico para success rate

Session entries NO usan estos campos:
- `timing_ms: 0` (session no tiene latencia)
- `warnings: []` (siempre vacío)
- `result.status`: N/A (usas `result.outcome`)

**CONSECUENCIA**:
Campos irrelevantes en session context → ruido cognitivo

**OPCIÓN**:
Filtrar estos campos al hacer `session query`:
```bash
trifecta session query --last 5 | jq 'del(.timing_ms, .warnings, .run_id)'
