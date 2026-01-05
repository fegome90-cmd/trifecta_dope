### Manual Testing

```bash
# Unit tests
uv run pytest tests/unit

# Acceptance tests
uv run pytest tests/acceptance -m "not slow"

# With coverage
uv run pytest --cov=src tests/
```

---
