# CI Quality Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Resolver los 3 problemas de calidad identificados: instalar safety scan, fix gradual de errores mypy, y documentar interacción entre sistemas de expansión.

**Architecture:** Mejoras graduales sin breaking changes. Prioridad: safety (rápido) → mypy (progresivo) → documentación (educativo). Cada tarea es atómica y commiteable.

**Tech Stack:** Python 3.13+, uv, mypy, safety, pytest

---

## Task 1: Install Safety Scan

**Files:**
- Verify: `pyproject.toml` (safety ya está listado)
- Command: terminal

**Step 1: Install safety**

```bash
uv pip install safety
```

Expected: Installation completes successfully

**Step 2: Verify installation**

```bash
which safety
safety --version
```

Expected: Path to binary and version number displayed

**Step 3: Run initial safety check**

```bash
uv run safety check
```

Expected: Report of dependencies with/without vulnerabilities

**Step 4: Commit**

```bash
git add -A  # If any lock files changed
git commit -m "chore(deps): install safety scan tool

- Add safety for dependency vulnerability scanning
- Run initial check to establish baseline"
```

---

## Task 2: Fix mypy type-arg Errors (Batch 1)

**Files:**
- Modify: `src/domain/anchor_extractor.py:1`
- Modify: `src/domain/query_linter.py:19,25,56,132`
- Modify: `src/domain/linear_policy.py:23,29,36,44,56,70`
- Test: `tests/unit/test_anchor_extractor.py`

**Step 1: Check current type-arg errors**

```bash
uv run mypy src/ --strict 2>&1 | grep "type-arg" | head -20
```

Expected: List of files with missing type parameters

**Step 2: Fix anchor_extractor.py**

```python
# src/domain/anchor_extractor.py line 1
from typing import Dict, List, Tuple, Any

# Change line 19 (if exists) from:
def process_anchors(data: dict) -> dict:
# To:
def process_anchors(data: dict[str, Any]) -> dict[str, Any]:
```

**Step 3: Fix query_linter.py**

```python
# src/domain/query_linter.py
# Line 19: Change dict to Dict[str, Any] or dict[str, Any]
# Line 25: Same pattern
# Line 56: Same pattern
# Line 132: Same pattern
```

Pattern: All `dict` → `dict[str, Any]` (or specific types if known)

**Step 4: Run mypy to verify fixes**

```bash
uv run mypy src/domain/anchor_extractor.py src/domain/query_linter.py --strict
```

Expected: No type-arg errors in these files

**Step 5: Run tests to ensure no breakage**

```bash
uv run pytest tests/unit/test_anchor_extractor.py tests/unit/test_query_linter.py -v
```

Expected: All tests pass

**Step 6: Commit**

```bash
git add src/domain/anchor_extractor.py src/domain/query_linter.py
git commit -m "fix(types): add type parameters to dict generics (batch 1)

- Fix type-arg errors in anchor_extractor.py
- Fix type-arg errors in query_linter.py
- Part of gradual mypy strict compliance"
```

---

## Task 3: Fix mypy type-arg Errors (Batch 2 - linear_policy)

**Files:**
- Modify: `src/domain/linear_policy.py`
- Test: `tests/unit/test_linear_policy.py` (if exists)

**Step 1: Fix linear_policy.py dict types**

```python
# src/domain/linear_policy.py
# Lines 23, 29, 36, 44, 56, 70
# Change all: dict → dict[str, Any]
# Or more specific if types are known from context
```

**Step 2: Verify fixes**

```bash
uv run mypy src/domain/linear_policy.py --strict
```

Expected: No type-arg errors

**Step 3: Run tests**

```bash
uv run pytest tests/unit/ -k linear -v
```

Expected: Tests pass

**Step 4: Commit**

```bash
git add src/domain/linear_policy.py
git commit -m "fix(types): add type parameters to linear_policy.py

- Fix 6 type-arg errors in dict generics
- Improves type safety for policy configuration"
```

---

## Task 4: Fix mypy unused-ignore Errors

**Files:**
- Modify: `src/infrastructure/alias_loader.py:12`

**Step 1: Find unused-ignore comments**

```bash
uv run mypy src/ --strict 2>&1 | grep "unused-ignore"
```

Expected: List of unnecessary `# type: ignore` comments

**Step 2: Remove unused ignore from alias_loader.py**

```python
# src/infrastructure/alias_loader.py line 12
# Remove:  # type: ignore
# Or keep if actually needed (re-run mypy to check)
```

**Step 3: Verify**

```bash
uv run mypy src/infrastructure/alias_loader.py --strict
```

Expected: No unused-ignore warnings

**Step 4: Commit**

```bash
git add src/infrastructure/alias_loader.py
git commit -m "chore(types): remove unused type: ignore comments

- Clean up alias_loader.py
- Reduces noise in mypy output"
```

---

## Task 5: Document Spanish Alias vs Linter Expansion

**Files:**
- Create: `docs/technical_guides/query_expansion_systems.md`
- Reference: `src/application/spanish_aliases.py`
- Reference: `src/domain/query_linter.py`

**Step 1: Create documentation file**

```markdown
# Query Expansion Systems

## Overview

Trifecta tiene **dos sistemas independientes** de expansión de queries:

1. **Linter Expansion** - Controlada por TRIFECTA_LINT
2. **Spanish Alias Expansion** - Siempre activa (condicional)

## Linter Expansion

### Trigger
- Queries vagas (1-2 tokens)
- Flag `TRIFECTA_LINT=1` o `--lint`

### Implementación
- Archivo: `src/domain/query_linter.py`
- Usa: `anchors.yaml` para expandir términos vagos

### Comportamiento A/B
- **OFF**: Query pasa sin modificación
- **ON**: Se añaden anchors strong/weak según clasificación

## Spanish Alias Expansion

### Trigger
- Query detectada como español
- Primera pasada (pass 1) retorna 0 hits
- No es fixture (`source != "fixture"`)

### Implementación
- Archivo: `src/application/spanish_aliases.py`
- Diccionario: `SPANISH_ALIASES` (español → inglés)
- Detección: `detect_spanish()` - caracteres, stopwords, aliases

### Comportamiento
```python
# Two-pass search en search_get_usecases.py:355-414
if len(final_hits) == 0 and detect_spanish(query):
    spanish_alias_variants = expand_with_spanish_aliases(query)
    # Re-intentar búsqueda con variantes en inglés
```

## Interacción entre Sistemas

### Caso Problemático (Resuelto)
```python
# Query: "servicio"
# LINT=OFF, pero Spanish Expansion activa:
#   "servicio" → "service"
#   "service" coincide con "ContextService" en chunk
# Resultado: 1 hit (inesperado si se esperaban 0)
```

### Solución
Usar queries que no triggeran Spanish Expansion:
- Evitar palabras en `SPANISH_ALIASES`
- Evitar caracteres españoles (áéíóúñ)
- Evitar stopwords españolas

Ejemplo: `"xyznonexistent"` no triggera ninguna expansión.

## Testing A/B Controlado

Para testear SOLO Linter Expansion:
1. No usar aliases.yaml (usa anchors.yaml)
2. No usar queries españolas
3. Usar queries vagas (1-2 tokens) en inglés

Ver: `tests/integration/test_ctx_search_linter_ab_controlled.py`
```

**Step 2: Verify documentation renders**

```bash
head -50 docs/technical_guides/query_expansion_systems.md
```

Expected: Content displays correctly

**Step 3: Commit**

```bash
git add docs/technical_guides/query_expansion_systems.md
git commit -m "docs: document query expansion systems interaction

- Explain Linter Expansion vs Spanish Alias Expansion
- Document the resolved issue with test_vague_spanish_query
- Provide testing guidelines for A/B controlled tests"
```

---

## Task 6: Verify Overall Improvements

**Files:**
- All modified files
- Verification commands

**Step 1: Run safety check**

```bash
uv run safety check --short-report
```

Expected: Clean report (or known vulnerabilities documented)

**Step 2: Check mypy progress**

```bash
uv run mypy src/ --strict 2>&1 | grep -c "error:"
```

Expected: Significantly less than 189 (target: <150 after batch 1-2)

**Step 3: Run affected tests**

```bash
uv run pytest tests/unit/test_anchor_extractor.py tests/unit/test_query_linter.py -v
```

Expected: All pass

**Step 4: Integration test for linter**

```bash
uv run pytest tests/integration/test_ctx_search_linter_ab_controlled.py -v
```

Expected: 3/3 PASSED

**Step 5: Final commit (if any remaining changes)**

```bash
git status
# Commit any remaining files
git add -A && git commit -m "chore: complete CI quality improvements batch"
```

---

## Summary

### Improvements Delivered

| Task | Improvement | Status Check |
|------|-------------|--------------|
| 1 | Safety scan installed | `safety --version` works |
| 2-3 | Mypy type-arg errors reduced | Error count < 150 |
| 4 | Unused ignores removed | No `unused-ignore` warnings |
| 5 | Documentation created | File exists and is readable |
| 6 | All tests pass | pytest exit 0 |

### Next Steps (Future Batches)

- Fix remaining `no-untyped-def` (31 errors)
- Fix remaining `no-untyped-call` (34 errors)
- Fix `no-any-return` (13 errors)
- Achieve 100% mypy strict compliance

---

## References

- @skill:superpowers:executing-plans - For implementing this plan
- @skill:superpowers:systematic-debugging - For analyzing type errors
- Commit 83cb92f - Original fix for test_vague_spanish_query
