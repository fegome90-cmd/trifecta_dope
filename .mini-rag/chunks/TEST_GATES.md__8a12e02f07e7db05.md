## Extended Gates (full verification)

```bash
# Slow tests (env-dependent, may require setup)
uv run pytest -q tests/acceptance -m slow

# Roadmap tests (unimplemented features)
uv run pytest -q tests/roadmap -m roadmap --ignore=

# Full suite
uv run pytest -q --no-header
```
