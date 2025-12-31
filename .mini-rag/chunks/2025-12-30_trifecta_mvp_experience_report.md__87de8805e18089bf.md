### Media Prioridad

4. **Synonym Expansion**
   ```yaml
   aliases:
     test: [pytest, unit, integration, validation]
     segment: [module, package, component]
   ```

5. **Session.md Automation**
   - Agregar `--auto-log` a cada comando ctx
   - Timestamp + command + ids automáticamente

6. **Budget-Aware Sorting**
   - Ordenar chunks por `token_est / relevance_score` (value per token)
   - Maximizar info en presupuesto dado

---
