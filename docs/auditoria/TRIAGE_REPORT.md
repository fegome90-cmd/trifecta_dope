# Triage Report — Ola 2 (54 failures + 10 errors)

**Fecha**: 2026-01-02  
**Baseline**: 287 passed, 54 failed, 10 errors  
**After Fixes**: 294 passed, 57 failed, **0 errors** ✅

---

## Resultado de Fixes Aplicados

| Fix | Impacto |
|-----|---------|
| SymbolResolver root optional | **10 errors → 0** ✅ |
| Telemetry reserved key validation | +3 passing reserved key tests |
| Total passed | 287 → 294 (+7) |

---

| # | Bucket | Count | Root Cause | Fix Lean |
|---|--------|-------|------------|----------|
| 1 | **PR2 Fixture Error** | 10 errors | `SymbolResolver.__init__()` missing `root` arg | Add optional root param |
| 2 | **Telemetry Reserved Keys** | 14 failures | Telemetry.event() no valida reserved keys | Agregar protección |
| 3 | **SymbolQuery API Mismatch** | 7 failures | Tests esperan `None`/attr, pero impl retorna `Err` | Ajustar tests o impl |
| 4 | **CLI Create Naming** | 4 failures | CLI args `--segment`/`--path` no existen en CLI actual | Ajustar tests |
| 5 | **AST Phase2a Strict** | 9 failures | Tests esperan APIs complejas no implementadas | Defer o skip |
| 6 | **T8 Observability** | 5 failures | Telemetry attrs missing (rotation, etc) | Agregar attrs |
| 7 | **Other** | 5 failures | Varios (counters, naming contract, etc) | Case by case |

---

## Evidencia por Bucket

### Bucket 1: PR2 Fixture Error (10 errors)

```
tests/unit/test_pr2_integration.py:53
TypeError: SymbolResolver.__init__() missing 1 required positional argument: 'root'
```

**Fix**:
```python
# src/application/symbol_selector.py
def __init__(self, builder: Any, root: Path = None):
```

**ROI**: 10 errors → 0 errors

---

### Bucket 2: Telemetry Reserved Keys (14 failures)

```
tests/unit/test_telemetry_extension.py:20: Failed: DID NOT RAISE <class 'ValueError'>
```

**Tests esperan**:
```python
with pytest.raises(ValueError, match="reserved keys"):
    telemetry.event("test", {}, {}, 100, ts="2026-01-01")  # ts is reserved
```

**Fix**: Agregar validación en `Telemetry.event()` para reserved keys.

**ROI**: 14 failures → 0 failures

---

### Bucket 3: SymbolQuery API Mismatch (7 failures)

```
tests/unit/test_ast_lsp_pr2.py:28: AttributeError: 'Err' object has no attribute 'language'
```

**Root cause**: Tests esperan `SymbolQuery.parse()` retorne `SymbolQuery | None`, pero impl retorna `Result[SymbolQuery, ASTError]`.

**Options**:
- A) Ajustar impl para retornar `SymbolQuery | None` (breaking other code?)
- B) Ajustar tests para usar `.ok()` pattern

**ROI**: 7 failures

---

### Bucket 4: CLI Create Naming (4 failures)

```
tests/unit/test_cli_create_naming.py:27: AssertionError: Create failed: assert 2 == 0
```

**Root cause**: Tests usan `--segment` y `--path` args que no existen en CLI actual (usa `-s`).

**Fix**: Ajustar tests a usar args correctos.

**ROI**: 4 failures

---

## Top 10 Acciones por ROI

| Priority | Action | Impact | Effort |
|----------|--------|--------|--------|
| 1 | Fix SymbolResolver.__init__ root param | -10 errors | 5 min |
| 2 | Add Telemetry reserved key protection | -14 failures | 15 min |
| 3 | Fix CLI create naming tests args | -4 failures | 5 min |
| 4 | Adjust SymbolQuery.parse tests for Result | -7 failures | 10 min |
| 5 | Add T8 Telemetry attrs (rotation, etc) | -5 failures | 20 min |
| 6 | Fix AST Phase2a tests or skip with reason | -9 failures | 30 min |
| 7 | Fix remaining "Other" tests | -5 failures | 30 min |

---

## Fixes Aplicados

### Fix 1: SymbolResolver root param (10 errors)

Cambiar `SymbolResolver.__init__` para hacer `root` opcional.

### Fix 2: Telemetry reserved key protection (14 failures)

Agregar validación en `event()`:
```python
RESERVED_KEYS = {"ts", "run_id", "segment_id", "cmd", "args", "result", "timing_ms", "warnings", "x"}
collisions = set(kwargs.keys()) & RESERVED_KEYS
if collisions:
    raise ValueError(f"Cannot use reserved keys: {collisions}")
```
