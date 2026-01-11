```diff
   - ### CRITICAL PROTOCOL: Session Evidence Persistence (Trifecta)
   -
   - Antes de ejecutar cualquier herramienta (Trifecta CLI o agentes externos), DEBES seguir este orden. NO tomes atajos.
   -
   - 1) PERSISTE intencion minima (CLI proactivo - NO depende del LLM):
   - ```bash
   - trifecta session append --segment . --summary "<que vas a hacer>" --files "<csv>" --commands "<csv>"
   - ```
   - [... 18 líneas más ...]

   + ### Session Evidence Protocol
   +
   + 1. **Persist**: `trifecta session append --segment . --summary "<task>"`
   + 2. **Sync**: `trifecta ctx sync --segment .`
   + 3. **Execute**: `ctx search` → `ctx get`
   + 4. **Record**: `trifecta session append --segment . --summary "Completed <task>"`
   +
   + > Ver [agent.md](./_ctx/agent_trifecta_dope.md) para comandos completos y protocolos detallados.
   ```

**Total eliminado/simplificado**: 22 líneas
