3. **Problema**: session.md no es queryable vía `ctx search` (no está en context pack)

   Reproducible:
   ```bash
   uv run trifecta ctx search -s . -q "LSP daemon" --limit 10 | jq '.[] | select(.doc == "session")'
   ```

   Output actual:
   ```
   (vacío - session.md no está indexado)
   ```

   Output esperado:
   ```json
   [{"id": "session:...", "preview": "Fixed LSP daemon...", ...}]
   ```

   Impacto CUANTIFICADO:
   - Tiempo perdido: ~3 min/búsqueda (cambiar de `ctx search` a grep manual)
   - Inconsistencia: Todos los docs están en ctx EXCEPTO session
   - Costo mental: Score 4/10 (recordar usar comando diferente para session)
   - Stakeholders afectados: 1

4. **Problema**: session.md contiene metadata no estructurada (parsing manual necesario)

   Reproducible:
   ```bash
   grep "## 2026-01-04" _ctx/session_trifecta_dope.md -A 10
   ```

   Output actual:
   ```markdown
   ## 2026-01-04T09:16:00-0300
   **Summary**: Created critical analysis doc for session JSONL proposal
   **Files**: docs/session_update/braindope_critical_analysis.md
   ```

   Output esperado (structured):
   ```json
   {"ts": "2026-01-04T09:16:00", "summary": "...", "files": ["..."], "type": "document"}
   ```
