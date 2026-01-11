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
