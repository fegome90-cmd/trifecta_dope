### Blocker 2: G1 pytest collecting (PRIORIDAD 2 — Tests = Evidencia)

**Hipótesis root-cause a confirmar:**
- Tests importan desde módulo incorrecto (AP9: compat shim en capa equivocada)
- `SymbolInfo` no existe (referencia fantasma)
- `_relpath` no existe en telemetry.py

**Herramientas de diagnóstico:**
```bash
# Buscar imports rotos (AP8: encontrar SSOT)
rg -n "from src.application.ast_parser import.*SymbolInfo" tests/
rg -n "from src.application.ast_parser import.*SkeletonMapBuilder" tests/
rg -n "from src.infrastructure.telemetry import.*_relpath" tests/

# Verificar dónde están realmente los símbolos
rg -n "class SkeletonMapBuilder|class SymbolInfo" src/
rg -n "def _relpath" src/

# Confirmar que SymbolInfo NO existe (debe retornar vacío)
rg -n "class SymbolInfo" src/
```

**Archivos candidatos:**
- `tests/unit/test_ast_lsp_pr2.py` — Línea 16: corregir import
- `tests/unit/test_pr2_integration.py` — Línea 14: corregir import
- `tests/unit/test_telemetry_extension.py` — Línea 10: corregir import
- `src/application/pr2_context_searcher.py` — Verificar si importa SymbolInfo
- `src/application/telemetry_pr2.py` — Verificar si importa SymbolInfo

**Patch mínimo (AP9: NO re-exports, arreglar imports):**

**1. test_ast_lsp_pr2.py:**
