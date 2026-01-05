# Validar entorno → Sync context → Ejecutar cambios → Validar gates
```

## Protocols

### Session Evidence Persistence

**Orden obligatorio** (NO tomes atajos):

1. **Persist Intent**:
   ```bash
   trifecta session append --segment . --summary "<que vas a hacer>" --files "<csv>" --commands "<csv>"
   ```

2. **Sync Context**:
   ```bash
   trifecta ctx sync --segment .
   ```

3. **Verify Registration** (confirma que se escribió en session.md)

4. **Execute Context Cycle**:
   ```bash
   trifecta ctx search --segment . --query "<tema>" --limit 6
   trifecta ctx get --segment . --ids "<id1>,<id2>" --mode excerpt --budget-token-est 900
   ```

5. **Record Result**:
   ```bash
   trifecta session append --segment . --summary "Completed <task>" --files "<touched>" --commands "<executed>"
   ```
```

---
