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

**Test tripwire:**
```bash
# Debe resolver sym://python/mod/context_service sin FILE_NOT_FOUND
uv run trifecta ast symbols sym://python/mod/context_service 2>/dev/null | \
  jq -r '.status, .errors[0].code // "null"'
# Esperado: "ok" o código != "FILE_NOT_FOUND"
echo "RC=$?"
```

**DoD:**
- [ ] `uv run trifecta ast symbols sym://python/mod/context_service` retorna `status: "ok"`
- [ ] `uv run trifecta ast symbols sym://python/mod/use_cases` funciona también
- [ ] Commit: "fix(g3): resolve FILE_NOT_FOUND with src/ convention"

---
