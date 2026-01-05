### 2) Tests vs Implementation
- **Tests esperan**: `SymbolInfo` existe en `ast_parser.py`
- **Implementación**: `ast_parser.py` solo tiene `ASTParser`
- **Evidencia**: `grep -r "class SymbolInfo" src/` returns nada
