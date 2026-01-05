### Bloqueador #2: PYTEST IMPORTERROR (ALTO)

**Archivos a tocar:**
1. `src/application/stubs.py` - NUEVO archivo con compat shims
2. `tests/unit/test_ast_lsp_pr2.py` - Actualizar imports
3. `tests/unit/test_telemetry_extension.py` - Actualizar imports

**DoD:**
- [ ] `uv run pytest -q` retorna `0 errors, X passed`
- [ ] Todos los imports resuelven sin ImportError
- [ ] No se borran tests sin ADR

**Compat Shims (src/application/stubs.py):**
```python
"""
Compatibility shims for legacy test imports.
DO NOT use in new code. Only for backward compatibility.
"""

# Stub for missing SymbolInfo (tests expect it)
class SymbolInfo:
    """Legacy stub. DO NOT USE in new code."""
    name: str
    kind: str

# Re-export _relpath if it was private
def relpath(path: Path) -> str:
    """Public wrapper for _relpath."""
    from src.infrastructure.telemetry import _relpath
    return _relpath(path)
```

**Comandos de verificación:**
```bash
# 1. Verificar pytest corre sin import errors
uv run pytest -q
# Expected: X passed in Y.ZZs (NO "ERROR collecting")

# 2. Verificar tests específicos pasan
uv run pytest tests/unit/test_ast_lsp_pr2.py -v
uv run pytest tests/unit/test_telemetry_extension.py -v
# Expected: PASSED
```

---
