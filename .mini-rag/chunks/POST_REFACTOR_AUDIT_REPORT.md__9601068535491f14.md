### TAREA C: Remover pytest.skip ✅

| Antes | Después |
|-------|---------|
| 9 `pytest.skip()` en test_pd_evidence_stop_e2e.py | 0 skips |
| 1 `@pytest.mark.skip` en test_cli_smoke_real_use.py | `@pytest.mark.slow` |

**Gate**: `tests/acceptance/test_no_skip_in_acceptance.py` (2 tests)

---
