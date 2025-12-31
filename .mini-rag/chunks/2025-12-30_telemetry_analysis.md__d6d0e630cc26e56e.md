#### Corto Plazo
1. **Indexar archivos faltantes:** 
   - `docs/plans/*.md`
   - `docs/walkthroughs/*.md`
   - Docstrings de clases key (Telemetry, validators)

2. **Implementar Query Suggestions:**
   ```python
   if hits == 0:
       suggestions = generate_related_queries(query)
       print("No results. Try: " + ", ".join(suggestions))
   ```

3. **Mostrar Alias Expansion:**
   ```
   🔍 Searching for: "telemetry"
   📝 Expanded with aliases: observability, logging, metrics, tracking
   ```
