## Implementation Sequence

| # | Task | File | Time | Priority |
|---|------|------|------|----------|
| 1 | Move validator to src/infrastructure/ | validators.py | 15m | HIGH |
| 2 | Update install_trifecta_context.py | scripts/ | 10m | HIGH |
| 3 | Update test imports | tests/installer_test.py | 5m | HIGH |
| 4 | Add exclusion list for skill.md | file_system.py | 10m | HIGH |
| 5 | Sync + validate context pack | _ctx/ | 5m | HIGH |
| 6 | Run gates (pytest, mypy, ruff) | tests/ | 10m | HIGH |

**Total**: ~55 minutes

---
