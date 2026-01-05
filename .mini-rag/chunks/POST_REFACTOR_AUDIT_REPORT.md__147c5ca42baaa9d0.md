## 2) Gates Globales

| Gate | Before | After |
|------|--------|-------|
| `pytest --collect-only` | ❌ 3 errors | ✅ 0 errors |
| `pytest -q` | Blocked | 286 passed, 55 failed, 10 errors |
| `mypy src` | 153 errors | 153 errors (unchanged) |
| `ruff check` | 98 errors | ~98 errors (unchanged) |

**Nota**: mypy/ruff errors son pre-existentes, NO del refactor Ola 1.

---
