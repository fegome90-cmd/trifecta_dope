#### 4. `ctx.refs` (Opcional)

```python
def ctx_refs(
    symbol_id: str,
    k: int = 5
) -> list[Reference]:
    """Get references to symbol."""

    refs = lsp.references(symbol_id)
    return refs[:k]
```

---
