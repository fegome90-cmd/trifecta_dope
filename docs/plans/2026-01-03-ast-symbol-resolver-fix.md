# AST/LSP Symbol Resolver Fix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix the AST/LSP Symbol Resolver to correctly resolve Python module paths using dot-to-slash conversion.

**Architecture:** Minimal fix to SymbolResolver.resolve() in symbol_selector.py (L94-95) to convert Python module paths (with dots) to filesystem paths (with slashes). TDD approach with failing test first.

**Tech Stack:** Python, pytest, uv

---

## Task 1: Fix SymbolResolver Dot-to-Slash Bug (RC1)

**Files:**
- Modify: `src/application/symbol_selector.py:91-116`
- Test: `tests/unit/test_symbol_selector_resolve.py` (NEW)

### Step 1: Write the failing test

Create file `tests/unit/test_symbol_selector_resolve.py`:

```python
"""Unit tests for SymbolResolver module path resolution."""
import pytest
from pathlib import Path
from src.application.symbol_selector import SymbolResolver, SymbolQuery, SkeletonMapBuilder


def test_symbol_resolver_converts_dots_to_slashes(tmp_path):
    """SymbolResolver should convert module dots to path slashes."""
    # Create a nested module structure
    (tmp_path / "src" / "infrastructure").mkdir(parents=True)
    (tmp_path / "src" / "infrastructure" / "telemetry.py").write_text("# test")

    resolver = SymbolResolver(builder=SkeletonMapBuilder(), root=tmp_path)
    query = SymbolQuery(kind="mod", path="src.infrastructure.telemetry")

    result = resolver.resolve(query)

    assert result.is_ok(), f"Expected Ok, got Err: {result}"
    candidate = result.unwrap()
    assert candidate.file_rel == "src/infrastructure/telemetry.py"


def test_symbol_resolver_handles_init_packages(tmp_path):
    """SymbolResolver should find __init__.py for package imports."""
    # Create a package with __init__.py
    (tmp_path / "src" / "domain").mkdir(parents=True)
    (tmp_path / "src" / "domain" / "__init__.py").write_text("# pkg")

    resolver = SymbolResolver(builder=SkeletonMapBuilder(), root=tmp_path)
    query = SymbolQuery(kind="mod", path="src.domain")

    result = resolver.resolve(query)

    assert result.is_ok(), f"Expected Ok, got Err: {result}"
    candidate = result.unwrap()
    assert candidate.file_rel == "src/domain/__init__.py"
```

### Step 2: Run test to verify it fails

```bash
uv run pytest tests/unit/test_symbol_selector_resolve.py -v
```

Expected: FAIL with "Expected Ok, got Err" (FILE_NOT_FOUND)

### Step 3: Write minimal implementation

Modify `src/application/symbol_selector.py:91-116`:

```python
def resolve(self, query: SymbolQuery) -> Result[Candidate, ASTError]:
    # Convert Python module path (dots) to filesystem path (slashes)
    path_as_dir = query.path.replace(".", "/")

    # Simple resolution logic
    candidate_file = self.root / f"{path_as_dir}.py"
    candidate_init = self.root / path_as_dir / "__init__.py"

    file_exists = candidate_file.exists() and candidate_file.is_file()
    init_exists = candidate_init.exists() and candidate_init.is_file()

    if file_exists and init_exists:
        return Err(
            ASTError(code=ASTErrorCode.AMBIGUOUS_SYMBOL, message="Ambiguous module path")
        )

    if file_exists:
        return Ok(Candidate(f"{path_as_dir}.py", "mod"))
    elif init_exists:
        return Ok(Candidate(f"{path_as_dir}/__init__.py", "mod"))

    return Err(
        ASTError(
            code=ASTErrorCode.FILE_NOT_FOUND, message=f"Could not find module for {query.path}"
        )
    )
```

### Step 4: Run test to verify it passes

```bash
uv run pytest tests/unit/test_symbol_selector_resolve.py -v
```

Expected: PASS (2 tests)

### Step 5: Commit

```bash
git add tests/unit/test_symbol_selector_resolve.py src/application/symbol_selector.py
git commit -m "fix(ast): convert dots to slashes in SymbolResolver module paths"
```

---

## Task 2: Update Workflow Documentation

**Files:**
- Modify: `.agent/workflows/trifecta-advanced.md`

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
