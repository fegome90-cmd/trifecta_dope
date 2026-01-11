## 0) Glosario y Sources of Truth

**TÉRMINOS CLAVE**:

1. **North Star**:
   Definición: "Un agente entienda cualquier segmento del repo en <60 segundos leyendo solo 3 archivos + 1 log"
   Documentado en: `README.md:L3`

2. **Session**:
   Definición: JSONL entry (event type `session.entry`) en telemetry que representa una tarea completada por el agente. NO es el archivo session.md (que es log humano generado).
   Documentado en: `docs/session_update/braindope_session_logging.md:L243-L254` + `FINAL_PROPOSAL.md:L15-L30`

3. **Context Pack**:
   Definición: Índice estructurado en `_ctx/context_pack.json` con digest + index + chunks, permite `ctx search` y `ctx get` bajo demanda.
   Documentado en: `README.md:L205-L253`

4. **Telemetry**:
   Definición: Sistema JSONL en `_ctx/telemetry/events.jsonl` que registra eventos de infraestructura (lsp.*, ast.*, ctx.*) con schema: ts, run_id, cmd, args, result, timing_ms, warnings, x.
   Documentado en: `docs/telemetry_event_schema.md:L1-L50`

5. **Programming Context Calling (PCC)**:
   Definición: Paradigma donde el agente invoca contexto como herramientas (`ctx search`, `ctx get`) en lugar de recibir todo el repo. Inspirado en artículo Anthropic advanced tool use.
   Documentado en: `README.md:L5-L43`
