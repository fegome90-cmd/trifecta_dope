### Implementación Pendiente
1. **session append** → Modificar para escribir a telemetry como `session.entry`
2. **session query** → CLI command que filtra telemetry por `cmd == "session.entry"`
3. **session load** → Wrapper de query que formatea para contexto
4. **Mitigaciones** (DECIDIDAS):
   - Query performance: grep filter + telemetry rotation (< 10K events)
   - Schema pollution: Filtrado automático (`--format clean`)
   - session.md: Se mantiene, generado desde JSONL (single source)
   - Bloat semántico: Convention-based namespace (`session.*` prefix + `x.category`)
