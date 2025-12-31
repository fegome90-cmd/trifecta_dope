#### 1. DocumentSymbols / WorkspaceSymbols

**Árbol de símbolos listo**:
```python
# LSP devuelve estructura completa
symbols = lsp.document_symbols("src/ingest.py")
# Perfecto para ctx.search sin heurísticas inventadas
```
