### 🥈 2. Replace `time.sleep` with Event-based Wait (P0 #2)
**Ahorro esperado**: 2-3 hours/sprint in flaky test retries  
**Esfuerzo**: 1 hour  
**Riesgo si no se hace**: CI flakes block deployments

```bash
# 1. Create tests/conftest.py::wait_for_condition helper
# 2. Apply to test_lsp_daemon.py (11 sites)
# 3. Add tripwire test
```

---
