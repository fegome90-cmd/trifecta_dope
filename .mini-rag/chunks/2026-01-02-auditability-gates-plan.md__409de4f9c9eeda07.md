### Blocker 3: G3 ast symbols (PRIORIDAD 3 — Contrato mínimo)

**Root-cause confirmado:**
- `SymbolResolver.resolve()` busca en `root` que por defecto es `.` (cwd)
- Módulos Python viven en `src/` fuera de cwd
- No existe concepto de "search paths"

**DECISIÓN: Convención fija `segment_root/src/` sin flags nuevos**

**Archivos a modificar:**
- `src/infrastructure/cli_ast.py` (línea 37: cálculo de root)
- `src/application/symbol_selector.py` (opcional: agregar search paths fallback)

**Patch mínimo:**

**1. cli_ast.py — Corregir cálculo de root:**
```python
# Antes (línea 37):
root = resolve_segment_root(Path(segment))

# Después (convención fija src/):
root = resolve_segment_root(Path(segment)) / "src"
# Nota: Si segment/ no existe segment/src, fallback a segment
```

**Versión robusta con fallback:**
```python
segment_root = resolve_segment_root(Path(segment))
src_dir = segment_root / "src"
if src_dir.exists() and src_dir.is_dir():
    root = src_dir
else:
    # Fallback para segmentos sin layout src/
    root = segment_root
```

**2. symbol_selector.py — Agregar search paths (opcional):**
