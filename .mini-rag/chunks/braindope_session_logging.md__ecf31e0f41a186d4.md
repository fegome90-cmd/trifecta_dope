**AHORA EL ATAQUE (problemas que NO consideraste)**:

```markdown
## PROBLEMAS CRÍTICOS (aún con la mejor versión)

### Problema #1: Query Performance Degradation
**REALIDAD**:
Telemetry JSONL crece RÁPIDO:
- Cada `ctx.sync` genera ~10 events
- Cada `lsp.request` genera 1 event
- Cada `ast.parse` genera 1 event

**ESCENARIO REAL (6 meses de uso)**:
- ~50K events en telemetry.jsonl
- Session entries: ~500 (1% del total)
- Query `session.entry` = lee 50K líneas para retornar 500

**COSTO**:
- Sin índice: O(n) = ~100-200ms para leer 50K líneas
- Con proyecto grande: 1-2 segundos

**MITIGACIÓN NECESARIA**:
```bash
