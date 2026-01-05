### 💀 Arquitectura: session_journal.jsonl separado
**Razón de Eliminación**: Usuario decidió reutilizar telemetry (no reinventar rueda)
**Ahorro Estimado**: ~10 horas (evita JSONL writer duplicado)
**Alternativa Adoptada**: Event type `session.entry` en telemetry existente

---
