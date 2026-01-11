### Alternativa A: Mejorar Telemetry Existente

**Idea**: Extender `_ctx/telemetry/events.jsonl` con session-level metadata.

**Pros**:
- ✅ Reutiliza infraestructura existente
- ✅ No duplica sistemas
- ✅ Ya tiene versionado de schema

**Contras**:
- ⚠️ Mezcla eventos fine-grained (commands) con coarse-grained (sessions)
- ⚠️ Telemetry puede tener propósito diferente (observability vs context)

---
