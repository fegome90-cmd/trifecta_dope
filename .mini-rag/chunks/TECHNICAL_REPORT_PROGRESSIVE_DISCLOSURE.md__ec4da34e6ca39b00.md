### 5.1 Comandos Disponibles

```bash
# Build & Index
uv run trifecta ctx sync -s .

# Search (L0)
uv run trifecta ctx search -s . -q "Verification"

# Get con modos (L0)
uv run trifecta ctx get -s . -i "skill:abc123" --mode skeleton
uv run trifecta ctx get -s . -i "skill:abc123" --mode excerpt
uv run trifecta ctx get -s . -i "skill:abc123" --mode raw

# AST/LSP (L1)
uv run trifecta ast symbols sym://python/mod/context_service
uv run trifecta ast hover src/application/context_service.py -l 50 -c 15
```
