### Para G1 (pytest collecting):
```bash
# Baseline rápido
uv run pytest --collect-only -q 2>&1; echo "RC=$?"

# Localizar primer fallo con detalle
uv run pytest --collect-only -q -k "test_" --maxfail=1 -vv 2>&1

# Buscar imports rotos
rg -n "ImportError|ModuleNotFoundError" tests/ -S

# Verificar imports específicos (todos deben fallar hoy)
python -c "from src.application.ast_parser import SymbolInfo" 2>&1  # EXPECTED FAIL
python -c "from src.application.symbol_selector import SkeletonMapBuilder" 2>&1  # EXPECTED PASS
python -c "from src.infrastructure.telemetry import _relpath" 2>&1  # EXPECTED FAIL

# Test tripwire: debe colectar sin errores
uv run pytest tests/unit/test_ast_lsp_pr2.py tests/unit/test_pr2_integration.py tests/unit/test_telemetry_extension.py --collect-only -q 2>&1 | grep -i "ERROR collecting" && echo "FAIL" || echo "PASS"
```
