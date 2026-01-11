### Reglas Inquebrantables
1. **telemetry.jsonl es source of truth** (session.md es generado)
2. **Schema output SIEMPRE limpio** (no exponer run_id, timing_ms a session context)
3. **Queries < 100ms** (vía grep filter + rotation)
4. **Token efficiency** (formato compact para contexto de agente)
