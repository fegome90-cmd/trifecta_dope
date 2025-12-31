### 5. Token Estimation

```python
def estimate_tokens(text: str) -> int:
    # Rough approximation: 1 token ≈ 4 characters
    return len(text) // 4
```

---
