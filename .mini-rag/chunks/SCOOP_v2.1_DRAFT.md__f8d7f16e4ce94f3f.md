d) **Plan de migración**: N/A (never existed)

   e) **Test de no-regresión**:
      ```bash
      ps aux | grep -i "session.*daemon" && exit 1 || exit 0
      ```

   **ELIMINATION GATE STATUS**: ✅ PASS (5/5)

4. **Feature**: session.md generado automáticamente en cada `session append`
   Por qué NO en V1: V2 (opcional - puede implementarse después)

   **ELIMINATION GATE**:

   a) **Casos de uso afectados**:
      - Caso 1: "Leer session como markdown humano" → Owner: Felipe → Impacto: Minor (puede usar `session query | jq`)

   b) **ROI de postergación**:
      Ahorro V1: 2 horas dev (script generador)
      Costo de NO tener: ~1 min/semana (comando query extra)
      Net: Postponer es razonable (low priority)

   c) **Reemplazo TEMPORAL**:
      Workaround V1: `session query --all | jq -r` para ver entries
      O mantener session.md manual (status quo)
      Pérdida: Sync automático .md ↔ JSONL
      Aceptada por: Felipe, 2026-01-04

   d) **Plan de migración**:
      V2: Implementar `session generate-md` command
      Deadline tentativo: 2026-02-01 (1 mes post-V1)
      Rollback: Mantener .md manual indefinidamente (acceptable)

   e) **Test de no-regresión**:
