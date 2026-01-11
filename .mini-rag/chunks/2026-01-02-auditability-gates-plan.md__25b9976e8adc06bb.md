```python
# Antes (línea 10):
from src.infrastructure.telemetry import Telemetry, _relpath
# Después:
from src.infrastructure.telemetry import Telemetry
# Reimplementar _relpath inline si se necesita:
def _relpath(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)
```

**Test tripwire:**
```bash
# Debe colectar todos los tests sin ImportError
uv run pytest --collect-only -q 2>&1 | tee /tmp/collect.log
grep -i "ERROR collecting" /tmp/collect.log
# EXITO si grep NO encuentra matches (RC=1)
echo "RC=$?"
```

**DoD:**
- [ ] `uv run pytest --collect-only -q` NO muestra "ERROR collecting"
- [ ] `uv run pytest tests/unit/test_ast_lsp_pr2.py --collect-only -q` pasa
- [ ] `uv run pytest tests/unit/test_pr2_integration.py --collect-only -q` pasa
- [ ] `uv run pytest tests/unit/test_telemetry_extension.py --collect-only -q` pasa
- [ ] Commit: "fix(g1): correct imports in test files"

---
