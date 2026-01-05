```python
# Antes (línea 16):
from src.application.ast_parser import SymbolInfo, SkeletonMapBuilder
# Después (AP9: import desde módulo dueño):
from src.application.symbol_selector import SkeletonMapBuilder
# Remover/usos de SymbolInfo (no existe en codebase)
```

**2. test_pr2_integration.py:**
```python
# Antes (línea 14):
from src.application.ast_parser import SkeletonMapBuilder, SymbolInfo
# Después (AP9):
from src.application.symbol_selector import SkeletonMapBuilder
# Actualizar usos de SymbolInfo si existen
```

**3. Verificar application/pr2_context_searcher.py y telemetry_pr2.py:**
- Si importan `SymbolInfo` de ast_parser, remover
- `SymbolInfo` no se usa en paths críticos (puede ser removido safe)

**4. test_telemetry_extension.py:**
```python
# Antes (línea 10):
from src.infrastructure.telemetry import Telemetry, _relpath
# Después:
from src.infrastructure.telemetry import Telemetry
# Reimplementar _relpath inline si se necesita (AP9: no compat shim)
def _relpath(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)
```

**Test tripwire:**
