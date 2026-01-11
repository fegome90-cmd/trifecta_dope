### Sincronización en `session append`
```bash
# Cuando ejecutas:
trifecta session append -s . --summary "..." --type debug ...

# Hace DOS cosas:
# 1. Append a telemetry.jsonl (source of truth)
# 2. Regenera session.md DESDE telemetry (opcional, si --sync-md flag)
```

**Single Source of Truth**: JSONL
**session.md**: Generado, humano-legible, NO se edita manual

---
