# Test Gates — Official Commands

## Default Gates (CI/local quick check)

```bash
# Core unit + integration (excludes roadmap)
uv run pytest -q

# Acceptance gate (excludes @slow)
uv run pytest -q tests/acceptance -m "not slow"
```

## Extended Gates (full verification)

```bash
# Slow tests (env-dependent, may require setup)
uv run pytest -q tests/acceptance -m slow

# Roadmap tests (unimplemented features)
uv run pytest -q tests/roadmap -m roadmap --ignore=

# Full suite
uv run pytest -q --no-header
```

## Markers

| Marker | Location | Meaning |
|--------|----------|---------|
| `@pytest.mark.slow` | tests/acceptance | Environment-dependent, slow |
| `@pytest.mark.roadmap` | tests/roadmap | Unimplemented features |

## Gate Policy

1. **Default run must be green** (no SKIP allowed)
2. **Slow = isolated**, run explicitly
3. **Roadmap = excluded** from default via `--ignore=tests/roadmap`
