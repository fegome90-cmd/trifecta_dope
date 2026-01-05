c) **Reemplazo o pérdida**:
      Reemplazo: Event type `session.entry` en telemetry.jsonl existente
      Pérdida: Pureza semántica (session y telemetry mezclados)
      Aceptada por: Felipe, 2026-01-04 (braindope Ronda 4)

   d) **Plan de migración**:
      No aplica (jamás existió)
      Rollback: N/A
      Escape hatch: Si en futuro se necesita separar, crear `session.jsonl` y migrar entries filtradas

   e) **Test de no-regresión**:
      ```bash
      # Verifica que NO existe session_journal.jsonl
      test ! -f _ctx/session_journal.jsonl
      ```

   **ELIMINATION GATE STATUS**: ✅ PASS (5/5 requisitos cumplidos)

3. **Feature**: Background script daemon para escribir session entries
   Por qué NO en V1: Nunca (operational risk alto)

   **ELIMINATION GATE**:

   a) **Casos de uso afectados**:
      - Caso 1: "Writes asincrónicos sin bloquear CLI" → Owner: Felipe → Impacto: Latencia de append +10ms síncrono (acceptable)

   b) **ROI de eliminación**:
      Ahorro: Cero supervisión, cero recovery logic, cero debugging de daemon muerto
      Costo de mantener: Infinite (daemon fallas silenciosas = data loss)
      Net: MASSIVE WIN (evita operational nightmare)

   c) **Reemplazo**:
      Reemplazo: Hook síncrono en `session append` (simple, confiable)
      Pérdida: Async writes (no necesario - write a JSONL es < 5ms)
      Aceptada por: Felipe, 2026-01-04
