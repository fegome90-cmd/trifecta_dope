### Router Mejorado: Intención + Señales

**Ya no por "archivo", sino por símbolo**:

```python
class SymbolRouter:
    def route(self, query: str, context: dict) -> list[str]:
        """Route based on intent + signals."""

        # Señales de intención
        mentioned_symbols = extract_symbols_from_query(query)
        mentioned_errors = extract_errors_from_query(query)

        # Señales del sistema (LSP)
        active_diagnostics = lsp.diagnostics(scope="hot")

        # Acción
        if mentioned_symbols:
            # Búsqueda por símbolo
            return ctx.search_symbol(mentioned_symbols[0])

        if mentioned_errors or active_diagnostics:
            # Contexto de error
            return ctx.get_error_context(active_diagnostics[0])

        # Fallback: búsqueda semántica
        return ctx.search(query, k=5)
```

---
