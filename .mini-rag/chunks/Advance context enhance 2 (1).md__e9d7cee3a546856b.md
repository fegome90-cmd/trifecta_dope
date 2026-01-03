### Example: Symbol-based retrieval

```python
def ctx_get_symbol(
    segment: str,
    symbol: str,
    file: str,
    context_lines: int = 5
) -> dict:
    """
    Retrieve a specific symbol with context.

    Uses LSP or Tree-sitter to locate the symbol,
    then returns it with surrounding lines.
    """
    pass
```

This is “GraphRAG for code” without the hype—just real structure.
