#### AGREGAR nueva sección "Protocols" (después de L51)

```markdown
## Protocols

### Session Evidence Persistence

**Orden obligatorio** (NO tomes atajos):

1. **Persist Intent**:
   ```bash
   trifecta session append --segment . --summary "<que vas a hacer>" --files "<csv>" --commands "<csv>"
   ```

1. **Sync Context**:

   ```bash
   trifecta ctx sync --segment .
   ```

2. **Verify Registration** (confirma que se escribió en session.md)

3. **Execute Context Cycle**:

   ```bash
   trifecta ctx search --segment . --query "<tema>" --limit 6
   trifecta ctx get --segment . --ids "<id1>,<id2>" --mode excerpt --budget-token-est 900
   ```

4. **Record Result**:

   ```bash
   trifecta session append --segment . --summary "Completed <task>" --files "<touched>" --commands "<executed>"
   ```

### STALE FAIL-CLOSED Protocol

**CRITICAL**: Si `ctx validate` falla o `stale_detected=true`:

1. **STOP** inmediatamente
2. **Execute**:

   ```bash
   trifecta ctx sync --segment .
   trifecta ctx validate --segment .
   ```

3. **Record** en session.md: `"Stale: true -> sync+validate executed"`
4. **Prohibido** continuar hasta PASS

**Prohibiciones**:

- YAML de historial largo
- Rutas absolutas fuera del segmento
- Scripts legacy de ingestion
- "Fallback silencioso"
- Continuar con pack stale

```

**Líneas agregadas**: +25
