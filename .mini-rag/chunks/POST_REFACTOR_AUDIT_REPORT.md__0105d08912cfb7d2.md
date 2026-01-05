### TAREA B: Eliminar time.sleep ✅

| Antes | Después |
|-------|---------|
| 11 `time.sleep()` en test_lsp_daemon.py | 0 sleeps largos |
| Tests flaky | `wait_for_condition()` polling |

**Archivos creados**:
- `tests/helpers.py` — `wait_for_condition(predicate, timeout=5.0, poll=0.05)`

**Tripwire**: `test_no_long_sleeps_in_lsp_daemon` verifica sin sleeps >0.5s
