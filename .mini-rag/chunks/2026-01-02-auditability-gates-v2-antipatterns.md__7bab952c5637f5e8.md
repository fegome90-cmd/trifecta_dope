```bash
# Debe colectar todos los tests sin ImportError (AP7: RC explícito)
uv run pytest --collect-only -q 2>&1 | tee /tmp/g1_collect.log
COLLECT_RC=${PIPESTATUS[0]}
grep -qi "ERROR collecting" /tmp/g1_collect.log && echo "FAIL" || echo "PASS (RC=$COLLECT_RC)"
```

**DoD:**
- [ ] `uv run pytest --collect-only -q` NO muestra "ERROR collecting"
- [ ] `uv run pytest tests/unit/test_ast_lsp_pr2.py --collect-only -q` pasa (RC=0)
- [ ] `uv run pytest tests/unit/test_pr2_integration.py --collect-only -q` pasa (RC=0)
- [ ] `uv run pytest tests/unit/test_telemetry_extension.py --collect-only -q` pasa (RC=0)
- [ ] Commit: "fix(g1): correct imports in tests (AP9: no re-exports)"

---
