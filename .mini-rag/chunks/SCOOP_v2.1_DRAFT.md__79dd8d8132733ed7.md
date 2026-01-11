c) **Reemplazo o pérdida**:
      Reemplazo: Flags `--files` y `--commands` (YA EXISTEN en `session append`)
      Pérdida aceptada: Felipe (owner) acepta escribir flags manualmente
      Firmado: 2026-01-04 (braindope convergencia Ronda 1)

   d) **Plan de migración**:
      No aplica (feature nunca existió - no hay migración)
      Rollback: N/A
      Escape hatch: N/A

   e) **Test de no-regresión**:
      ```bash
      # Verifica que NO hay parser de tool use en código
      rg "parse.*tool.*use|detect.*files.*touched" src/ && exit 1 || exit 0
      ```

   **ELIMINATION GATE STATUS**: ✅ PASS (5/5 requisitos cumplidos)

2. **Feature**: session_journal.jsonl (JSONL separado de telemetry)
   Por qué NO en V1: Nunca (decisión arquitectónica - reutilizar telemetry)

   **ELIMINATION GATE**:

   a) **Casos de uso afectados**:
      - Caso 1: "Separación semántica limpia de session vs observability" → Owner: Felipe → Impacto: Purismo arquitectónico (no funcional)
      - Caso 2: Ningún otro

   b) **ROI de eliminación**:
      Ahorro: 10 horas dev (JSONL writer duplicado) + 15 puntos complejidad + cero bugs de sincronización
      Costo de mantener: Mixing "narrative" (session) con "metrics" (telemetry) = ~0 horas (pragmatismo > pureza)
      Net: POSITIVO (+10h ahorro, costo conceptual aceptable)
