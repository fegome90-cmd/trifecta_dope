## 6) Alcance V1 + ELIMINATION GATE

**V1 - ESTO SÍ**:

1. Modificar `trifecta session append` para escribir event type `session.entry` a `_ctx/telemetry/events.jsonl`
2. Implementar `trifecta session query` con filtros (--type, --last, --since, --tag, --outcome)
3. Schema limpio: filtrar campos telemetry irrelevantes (run_id, timing_ms, warnings) al hacer query
4. Grep optimization: `session query` usa `grep '"cmd": "session.entry"'` antes de jq para performance
5. Tests E2E para workflows críticos (append, query, load)

**CEMENTERIO - ESTO NO (ELIMINATION GATE OBLIGATORIO)**:

1. **Feature**: Auto-detección automática de tool use
   Por qué NO en V1: Nunca (eliminaciónsay permanente)

   **ELIMINATION GATE**:

   a) **Casos de uso afectados**:
      - Caso 1: "Agente registra files touched sin flag manual" → Owner: Felipe → Impacto: Conveniencia (no blocker)
      - Caso 2: Ningún otro caso conocido

   b) **ROI de eliminación**:
      Ahorro: 15 horas dev (parser complejo) + 10 puntos complejidad
      Costo de mantener: ~5 horas/mes (parser se rompe con cambios en output del agente)
      Net: POSITIVO (+15h -5h/m indefinido = massive win)
