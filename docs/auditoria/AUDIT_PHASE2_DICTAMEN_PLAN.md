# AUDITORÍA FASE 2 - DICTAMEN + PLAN MÍNIMO
**Fecha**: 2026-01-02
**SHA**: bb615dfdc3ce62b5139d1f27fa8f376b21dd5b09
**Método**: Systematic Debugging (Phase 1-2 completado)

---

## A) Hallazgos (Evidencia Verificada)

| # | Hallazgo | Severidad | Evidencia (archivo:línea) | Impacto | Recomendación |
|---|----------|-----------|---------------------------|---------|---------------|
| 1 | **PATH HYGIENE VIOLATION** | CRÍTICA | `_ctx/context_pack.json` contiene `/Users/felipe_gonzalez/Developer/agent_h` | PII expuesto, no portable | Sanitizar rutas en write + test tripwire |
| 2 | **pytest ImportError (3 files)** | ALTA | `test_ast_lsp_pr2.py:16`, `test_pr2_integration.py:12`, `test_telemetry_extension.py:10` | Tests no ejecutan, feedback perdido | Crear compat shims o arreglar imports |
| 3 | **SymbolInfo no existe** | ALTA | Tests importan `SymbolInfo` de `ast_parser`, grep returns nada | Bloquea tests PR2 | Definir clase o stub compatible |
| 4 | **_relpath privado expuesto** | MEDIA | `test_telemetry_extension.py:10` importa `_relpath` (privado) | Violación encapsulación | Usar API pública o re-exportar |
| 5 | **LSP output skeleton-only** | MEDIA | `cli_ast.py:259-268` siempre retorna skeleton, ignora response LSP real | LSP no aporta valor real | Retornar response LSP o quitar daemon |
| 6 | **ast symbols FILE_NOT_FOUND** | MEDIA | `trifecta ast symbols sym://python/mod/context_service` → error | Feature L1 rota | Corregir SymbolResolver |
| 7 | **Lock mechanisms duplicados** | BAJA | `fcntl.flock` (file_system_utils.py:40) vs `fcntl.lockf` (lsp_daemon.py:50) | Confusión, dos APIs | Documentar o unificar |
| 8 | **Segment name vs path hash** | BAJA | `normalize_segment_id()` (string) vs `compute_segment_id()` (SHA256) | Nombres confusos pero funcional | Renombrar para claridad |

**NOTA IMPORTANTE**: ContextPack NO está duplicado. El reporte SCOPE FASE 1 tuvo un error de grep:
- `src/domain/context_models.py:39` = Pydantic ContextPack (SSOT real)
- `src/domain/models.py` = NO tiene ContextPack (el grep original malinterpretó)

---

## B) Contradicciones Detectadas

### 1) Docs vs Runtime (PATH HYGIENE)
- **Doc dice**: "Audit: No PII, No VFS, Sanitized Paths" (`agent_trifecta_dope.md` line 69)
- **Runtime hace**: Escribe `/Users/felipe_gonzalez/Developer/agent_h` en `context_pack.json`
- **Evidencia**: `grep -n "repo_root.*Users" _ctx/context_pack.json` retorna matches

### 2) Tests vs Implementation
- **Tests esperan**: `SymbolInfo` existe en `ast_parser.py`
- **Implementación**: `ast_parser.py` solo tiene `ASTParser`
- **Evidencia**: `grep -r "class SymbolInfo" src/` returns nada

### 3) LSP Contract
- **Doc dice**: "LSP deje de ser latente y aporte valor real"
- **Runtime hace**: `ast hover` siempre retorna skeleton vacío, ignora response LSP
- **Evidencia**: `cli_ast.py:259-268` hardcodea skeleton response

---

## C) Dictamen

### **AUDITABLE-PARTIAL-PASS**

**Justificación (3 líneas):**
1. Sistema funcional para PD L0 (skeleton/excerpt/raw) con telemetría robusta (timing_ms>=1).
2. **BLOCKERS**: PII en `context_pack.json` + 3 tests con ImportError + feature `ast symbols` rota.
3. **NO CRÍTICO**: LSP daemon funciona pero output no se usa; locks duplicados pero no race conditions.

**Breakdown:**
- **PASS**: Telemetría, PD L0, segment_id hash determinista, daemon lifecycle
- **PARTIAL**: Tests (3/?), LSP value prop, path hygiene
- **FAIL**: N/A (no hay rotación de datos)

---

## D) Plan Mínimo (Patches MUST-FIX)

### Bloqueador #1: PATH HYGIENE (CRÍTICO)

**Archivos a tocar:**
1. `src/application/use_cases.py` - DONDE escribe el pack con rutas absolutas
2. `tests/integration/test_path_hygiene.py` - NUEVO test tripwire

**DoD:**
- [ ] `context_pack.json` NO contiene `/Users/` o `/home/` después de `ctx sync`
- [ ] Test tripwire detecta rutas absolutas y falla
- [ ] Chunks con rutas absolutas se sanitizan en write-time

**Test Tripwire:**
```python
# tests/integration/test_path_hygiene.py
def test_context_pack_no_absolute_paths(tmp_path):
    """FAIL if any absolute path leaks into context_pack.json or chunks."""
    # Run ctx sync
    # Load context_pack.json
    # Assert no /Users/ or /home/ in any field
```

**Comandos de verificación:**
```bash
# 1. Sync para generar pack
uv run trifecta ctx sync -s .

# 2. Verificar NO hay paths absolutos
grep -E '"/Users/|"/home/' _ctx/context_pack.json
# Expected: NO OUTPUT (exit code 1)

# 3. Verificar test pasa
uv run pytest tests/integration/test_path_hygiene.py -v
# Expected: PASSED
```

---

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

### Bloqueador #3: AST SYMBOLS FILE_NOT_FOUND (MEDIO)

**Archivos a tocar:**
1. `src/application/symbol_selector.py` - DONDE está `SkeletonMapBuilder`
2. `src/infrastructure/cli_ast.py` - DONDE se falla con FILE_NOT_FOUND
3. `tests/integration/test_ast_symbols.py` - NUEVO test

**DoD:**
- [ ] `trifecta ast symbols sym://python/mod/context_service` retorna data válida
- [ ] Test de integración verifica comando funciona
- [ ] SymbolResolver encuentra módulos existentes

**Comandos de verificación:**
```bash
# 1. Verificar comando funciona
uv run trifecta ast symbols sym://python/mod/context_service
# Expected: JSON con "status": "ok" y children no vacío

# 2. Verificar test pasa
uv run pytest tests/integration/test_ast_symbols.py -v
# Expected: PASSED
```

---

## E) Evidencia Requerida (Outputs Crudos)

**Usuario debe pegar estos outputs para cerrar PASS:**

### E1: Path Hygiene Verificado
```bash
$ uv run trifecta ctx sync -s .
[output completo]

$ grep -E '"/Users/|"/home/' _ctx/context_pack.json
# Expected: NO OUTPUT (exit code 1)

$ uv run pytest tests/integration/test_path_hygiene.py -v
# Expected: test_no_absolute_paths PASSED
```

### E2: Pytest Collection OK
```bash
$ uv run pytest -q
# Expected: X passed in Y.ZZs (SIN "ERROR collecting")
```

### E3: AST Symbols Funciona
```bash
$ uv run trifecta ast symbols sym://python/mod/context_service
# Expected: {"status": "ok", "kind": "skeleton", "data": {"children": [...]}}
```

---

## F) Preguntas (Máx 3)

**Q1**: ¿Es aceptable crear `stubs.py` para compatibilidad o preferís eliminar tests obsoletos?

**Q2**: ¿LSP daemon debe mantenerse si output no se usa (skeleton-only) o se remueve para simplificar?

**Q3**: ¿`segment_id` debe ser siempre SHA256 del path (determinista) o puede ser el nombre normalizado (humano-readable)?

---

**FIN DE FASE 2 - Esperando respuesta a Q1-Q3 para implementar patch.**
