### Tool 1: `ctx.search`

**Propósito**: Buscar chunks relevantes

```python
def ctx_search(
    segment: str,
    query: str,
    k: int = 5,
    filters: Optional[dict] = None
) -> SearchResult:
    """
    Busca chunks relevantes en el context pack.

    Returns:
        {
            "hits": [
                {
                    "id": "skill-core-rules-abc123",
                    "title_path": ["Core Rules", "Sync First"],
                    "preview": "1. **Sync First**: Validate .env...",
                    "token_est": 150,
                    "source_path": "skill.md",
                    "score": 0.92
                }
            ]
        }
    """
```
