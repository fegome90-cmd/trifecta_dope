### Bloqueador #3: AST SYMBOLS FILE_NOT_FOUND (MEDIO)

**Archivos a tocar:**
1. `src/application/symbol_selector.py` - DONDE está `SkeletonMapBuilder`
2. `src/infrastructure/cli_ast.py` - DONDE se falla con FILE_NOT_FOUND
3. `tests/integration/test_ast_symbols.py` - NUEVO test

**DoD:**
- [ ] `trifecta ast symbols sym://python/mod/context_service` retorna data válida
- [ ] Test de integración verifica comando funciona
- [ ] SymbolResolver encuentra módulos existentes

**Comandos de verificación:**
```bash
# 1. Verificar comando funciona
uv run trifecta ast symbols sym://python/mod/context_service
# Expected: JSON con "status": "ok" y children no vacío

# 2. Verificar test pasa
uv run pytest tests/integration/test_ast_symbols.py -v
# Expected: PASSED
```

---
