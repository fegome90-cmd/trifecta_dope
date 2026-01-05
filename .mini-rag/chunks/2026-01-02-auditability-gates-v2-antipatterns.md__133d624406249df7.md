### Blocker 3: G3 ast symbols (PRIORIDAD 3 — Contrato mínimo)

**Hipótesis root-cause a confirmar:**
- `SymbolResolver.resolve()` busca en `root` que por defecto es `.` (cwd) (AP3)
- Módulos Python viven en `src/` fuera de cwd
- No existe concepto de "search paths" o convención src/

**Herramientas de diagnóstico:**
```bash
# Localizar cálculo de root en cli_ast.py (AP8: SSOT)
rg -n "resolve_segment_root|Path\(segment\)|root =" src/infrastructure/cli_ast.py

# Localizar lógica de resolución en symbol_selector.py
rg -n "def resolve|candidate_file|candidate_init|FILE_NOT_FOUND" src/application/symbol_selector.py

# Probar desde diferentes cwds (AP3 tripwire)
cd /tmp && uv run trifecta ast symbols sym://python/mod/context_service
# Esperado hoy: FILE_NOT_FOUND (porque busca en /tmp)
```

**Archivos candidatos:**
- `src/infrastructure/cli_ast.py` — Línea 37: cálculo de `root`
- `src/application/symbol_selector.py` — Método `resolve()`

**Patch mínimo (AP3: segment_root/src/ convención, AP5: precedencia clara):**

**1. cli_ast.py — Corregir cálculo de root:**
