Impacto CUANTIFICADO:
   - Tiempo perdido: ~2 horas implementando parser ad-hoc si se necesita
   - Bugs potenciales: Markdown parsing frágil (headings cambian formato)
   - Stakeholders afectados: 1

5. **Problema**: Telemetry ya tiene toda la infraestructura (JSONL, rotation, schema) pero session no la usa

   Reproducible:
   ```bash
   ls _ctx/telemetry/
   # vs
   ls _ctx/session*.jsonl 2>&1
   ```

   Output actual:
   ```
   _ctx/telemetry/events.jsonl
   _ctx/telemetry/last_run.json

   ls: _ctx/session*.jsonl: No such file or directory
   ```

   Output esperado:
   ```
   Session entries están EN telemetry.jsonl como event type
   ```

   Impacto CUANTIFICADO:
   - Deuda técnica: Duplicación de infra si se crea session_journal.jsonl separado (~10 horas dev)
   - Complejidad: +15 puntos si se añade segundo JSONL
   - Mantenimiento: 2 schemas forever vs 1
   - Stakeholders afectados: 1 (Felipe - único maintainer)

---
