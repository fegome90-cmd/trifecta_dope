#### `ast hover`
```bash
uv run trifecta ast hover src/application/context_service.py -l 50 -c 15
```

**Flujo**:
1. Spawn/connect LSP Daemon
2. Warm wait hasta 200ms
3. Si READY → `textDocument/hover` request
4. Si no → Fallback a AST skeleton

---
