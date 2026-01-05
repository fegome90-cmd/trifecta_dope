#### 1. `ctx.search`

```python
def ctx_search(
    query: str,
    k: int = 5,
    scope: Literal["hot", "project"] = "hot"
) -> SearchResult:
    """Search using LSP symbols if available, else AST index."""

    if lsp_available:
        symbols = lsp.workspace_symbols(query)
    else:
        symbols = ast_index.search(query)

    return filter_by_score(symbols, k)
```
