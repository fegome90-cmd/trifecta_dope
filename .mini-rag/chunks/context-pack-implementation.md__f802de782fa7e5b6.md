### Token Estimation

```python
def estimate_tokens(text: str) -> int:
    """Rough token estimation: 1 token ≈ 4 characters."""
    return len(text) // 4
```

> **Nota**: Estimación aproximada. Para tokens exactos, usar tokenizer del modelo.

---
