### How it works

Your “Context Pack” is a library of invokable pieces, but you don’t define “one tool per chunk.” Instead, you define two tools:

```python
# Runtime tools (not in the pack itself)

def ctx_search(
    segment: str,
    query: str,
    k: int = 6,
    doc: str | None = None
) -> list[dict]:
    """
    Search for relevant context chunks.

    Returns:
        list of {
            id: str,
            doc: str,
            title_path: list[str],
            preview: str,
            token_est: int,
            source_path: str,
            score: float
        }
    """
    pass

def ctx_get(
    segment: str,
    ids: list[str],
    mode: str = "excerpt",
    budget_token_est: int = 1200
) -> list[dict]:
    """
    Retrieve specific chunks within token budget.

    Args:
        mode: "excerpt" | "raw" | "skeleton"
        budget_token_est: maximum tokens to return

    Returns:
        list of {
            id: str,
            title_path: list[str],
            text: str
        }
    """
    pass
```

This enables true progressive disclosure: cheap navigation first, specific evidence second.
