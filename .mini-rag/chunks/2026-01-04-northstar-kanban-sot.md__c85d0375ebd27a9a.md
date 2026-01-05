## Task 3: Mapear Items del Roadmap a Código

**Files:**
- Modify: `docs/v2_roadmap/TRIFECTA_NORTHSTAR_KANBAN.md` (o `.kanban.md`)

**Step 3.1: Para cada item del roadmap, verificar estado en código**

Para cada item, ejecutar:

```bash
# Ejemplo: Verificar "Result Monad"
uv run trifecta ctx search -s . -q "Result Monad Ok Err"
rg "class Ok" src/
```

**Step 3.2: Crear matriz de trazabilidad**

| Item Roadmap | Path Código | Test Path | Estado |
| :--- | :--- | :--- | :--- |
| Result Monad | `src/domain/result.py` | `tests/unit/test_result_monad.py` | ✅ |
| North Star Gate | `src/infrastructure/validators.py` | `tests/unit/test_validators_fp.py` | ✅ |
| Progressive Disclosure | `src/application/context_service.py` | `tests/unit/test_chunking.py` | ✅ |

**Step 3.3: Identificar Ghost Implementations**

Buscar clases sin llamadas en la aplicación:

```bash
rg "class SymbolSelector" src/  # Existe
rg "SymbolSelector" src/application/use_cases.py  # ¿Se usa?
```

---
