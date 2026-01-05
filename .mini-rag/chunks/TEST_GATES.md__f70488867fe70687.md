## Default Gates (CI/local quick check)

```bash
# Core unit + integration (excludes roadmap)
uv run pytest -q

# Acceptance gate (excludes @slow)
uv run pytest -q tests/acceptance -m "not slow"
```
