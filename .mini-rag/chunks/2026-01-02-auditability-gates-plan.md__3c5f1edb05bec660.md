### Blocker 2: G1 pytest collecting (PRIORIDAD 2 — Tests = Evidencia)

**Root-cause confirmado:**
- Tests importan símbolos desde módulos incorrectos
- `SymbolInfo` no existe (referencia fantasma)
- `_relpath` no existe en telemetry.py

**DECISIÓN: Opción B — Corregir imports en tests (NO re-exports)**

**Archivos a modificar:**
- `tests/unit/test_ast_lsp_pr2.py` (línea 16)
- `tests/unit/test_pr2_integration.py` (línea 14 y usos)
- `tests/unit/test_telemetry_extension.py` (línea 10 y usos)

**Patch mínimo:**

**1. test_ast_lsp_pr2.py:**
```python
# Antes (línea 16):
from src.application.ast_parser import SymbolInfo, SkeletonMapBuilder
# Después:
from src.application.symbol_selector import SkeletonMapBuilder
# Remover cualquier uso de SymbolInfo (no existe)
```

**2. test_pr2_integration.py:**
```python
# Antes (línea 14):
from src.application.ast_parser import SkeletonMapBuilder, SymbolInfo
# Después:
from src.application.symbol_selector import SkeletonMapBuilder
# Actualizar usos de SymbolInfo si existen
```

**3. Verificar/application/pr2_context_searcher.py y telemetry_pr2.py:**
- Si importan `SymbolInfo` de ast_parser, remover esa import
- `SymbolInfo` no se usa en paths críticos actualmente

**4. test_telemetry_extension.py:**
