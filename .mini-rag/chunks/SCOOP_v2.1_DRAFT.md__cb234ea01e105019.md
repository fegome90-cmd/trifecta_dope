## 5) Dolor actual (evidencia cuantificada)

1. **Problema**: session.md crece indefinidamente sin archivado automático

   Reproducible:
   ```bash
   wc -l _ctx/session_trifecta_dope.md
   ```

   Output actual:
   ```
   397 _ctx/session_trifecta_dope.md
   ```

   Output esperado:
   ```
   < 100 líneas (últimas ~20 entradas, resto archivado)
   ```

   Impacto CUANTIFICADO:
   - Tiempo perdido: ~5 min/semana navegando archivo grande
   - Tokens desperdiciados: 5165 tokens si se carga completo (viola North Star <60s)
   - Costo mental: Score 6/10 (confusión sobre qué entries son relevantes)
   - Stakeholders afectados: 1 (Felipe - único dev actual)

2. **Problema**: No hay forma de query session por tipo/fecha/tags

   Reproducible:
   ```bash
   # Intento buscar entradas de debug en último mes
   uv run trifecta session query -s . --type debug 2>&1
   ```

   Output actual:
   ```
   Error: Unknown command 'query'
   ```

   Output esperado:
   ```json
   [{"ts": "...", "summary": "...", "type": "debug", ...}]
   ```

   Impacto CUANTIFICADO:
   - Tiempo perdido: ~10 min/hora buscando manualmente en session.md
   - Bugs: 0 directo, pero dificulta debugging post-mortem
   - Frecuencia de uso futuro: Estimado 5-10 queries/hora cuando CLI en uso activo
   - Stakeholders afectados: 1 (Felipe)
