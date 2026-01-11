```python
# Antes (línea 37):
root = resolve_segment_root(Path(segment))
# AP3 PROBLEMA: root = cwd cuando segment="."

# Después (convención fija src/ con fallback):
segment_root = resolve_segment_root(Path(segment))
src_dir = segment_root / "src"

# AP5: Precedencia explícita: convención src/ primero, fallback si no existe
if src_dir.exists() and src_dir.is_dir():
    root = src_dir
else:
    # Fallback para segmentos sin layout src/
    root = segment_root
```

**Versión alternativa con search paths (opcional, NO agregar flag):**
```python
# En SymbolResolver.resolve(), antes de retornar FILE_NOT_FOUND:
SEARCH_PATHS = ["", "src/", "src/application/", "src/infrastructure/"]

for search_path in SEARCH_PATHS:
    candidate_with_path = self.root / search_path / f"{query.path}.py"
    init_with_path = self.root / search_path / query.path / "__init__.py"

    if candidate_with_path.exists() and candidate_with_path.is_file():
        return Ok(Candidate(f"{search_path}{query.path}.py", "mod"))
    if init_with_path.exists() and init_with_path.is_file():
        return Ok(Candidate(f"{search_path}{query.path}/__init__.py", "mod"))
```

**CWD Independence test (AP3 TRIPWIRE para G3):**
