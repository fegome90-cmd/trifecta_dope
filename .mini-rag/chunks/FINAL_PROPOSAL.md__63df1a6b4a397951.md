## CLI Interface Final

```bash
# Append session entry (escribe a telemetry + sync md)
trifecta session append -s . \
  --summary "Fixed LSP bug" \
  --type debug \
  --files "src/lsp.py,src/daemon.py" \
  --commands "pytest tests/,ruff check" \
  --outcome success \
  --tags "lsp,daemon" \
  --sync-md  # Opcional: regenera session.md

# Query (output limpio, sin campos telemetry)
trifecta session query -s . \
  --type debug \
  --last 10 \
  --format clean  # Default: clean (sin run_id, timing_ms, etc.)

# Query raw (si necesitas schema completo)
trifecta session query -s . --last 5 --format raw

# Load context (para agente - máximo token efficiency)
trifecta session load -s . --last 3 --format compact
# Output: Solo summary + type en 1 línea por entry
```

---
