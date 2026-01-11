### CLI Interface
```bash
# Agregar session entry (extendiendo comando existente)
trifecta session append -s . \
  --summary "Fixed LSP bug" \
  --type debug \
  --files "src/lsp.py" \
  --commands "pytest tests/" \
  --outcome success \
  --tags "lsp,daemon"

# Query session entries
trifecta session query -s . --type debug --last 10
trifecta session query -s . --tag lsp --since 2026-01-01
trifecta session query -s . --outcome failed  # Buscar fracasos

# Load session context (via ctx-like interface)
trifecta session load -s . --last 5  # Carga últimas 5 entries como contexto
```
