### Step 1: Add [WIP] warnings and correct DSL format

Update the workflow to warn about incomplete functionality:

```markdown
## ⚠️ Estado del Sistema AST/LSP

> **[WIP]**: Los comandos `ast symbols` están en desarrollo.
> El fallback `grep` es más confiable para búsquedas rápidas.

## Formato URI Correcto

```
sym://python/<kind>/<module.path>

Donde:
- <kind>: "mod" (módulo) o "type" (clase)
- <module.path>: ruta con puntos (ej: src.infrastructure.telemetry)
```

### Step 2: Commit

```bash
git add .agent/workflows/trifecta-advanced.md
git commit -m "docs(workflow): mark AST commands as WIP, document correct URI format"
```

---

## Task 3: Verify Fix with CLI

### Step 1: Run integration test

```bash
uv run trifecta ast symbols "sym://python/mod/src.infrastructure.telemetry" --segment .
```

Expected: JSON response with `status: "ok"` and resolved file path

### Step 2: Run full test suite

```bash
uv run pytest tests/ -m "not slow" --ignore=tests/roadmap -q
```

Expected: All tests pass

### Step 3: Final commit

```bash
git add -A
git commit -m "chore: verify AST symbol resolution fix"
git push
```

---

## Summary

| Task | Description | Time Est. |
|------|-------------|-----------|
| 1 | Fix SymbolResolver dots-to-slashes | 10 min |
| 2 | Update workflow docs | 5 min |
| 3 | Verify with CLI + tests | 5 min |

**Total: ~20 minutes**
