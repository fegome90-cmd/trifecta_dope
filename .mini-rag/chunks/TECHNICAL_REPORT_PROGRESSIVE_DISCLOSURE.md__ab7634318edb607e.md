#### `ast symbols`
```bash
uv run trifecta ast symbols sym://python/mod/context_service/ContextService
```

**Flujo**:
1. Parse URI → `SymbolQuery`
2. `SymbolResolver` resuelve a archivo
3. Check LSP readiness → Fallback a AST si no ready
4. Parse con ASTParser → Output skeleton JSON
