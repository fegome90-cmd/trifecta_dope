# Plan: Fix Search Context Preview Truncation

**Branch**: `fix/search-context-preview-truncation`
**Fecha**: 2026-03-29
**Objetivo**: Resolver el problema donde el motor de búsqueda solo busca en previews truncados (~200 chars) en vez del texto completo del chunk.

---

## Problema

1. `context_pack.json` tiene 2 secciones: `chunks` (texto completo) y `index` (previews truncados ~200 chars)
2. `ContextService.search()` busca solo en `index[i].preview` e `index[i].title_path_norm`
3. Los previews están truncados a ~200 chars — 95.4% terminan en `...`
4. Las keywords reales (pytest, fixtures, mocking) están en el chunk text pero fueron cortadas del preview
5. Las queries en español generan palabras que no existen en el preview truncado

---

## Fases de Implementación

### Fase 1: Quick Fix (Preview Length)

**Objetivo**: Aumentar preview de 200 a 500 chars para resolver 80% del problema

| Task | Archivo | Cambio | Commit |
|------|---------|--------|--------|
| 1.1 | `src/application/use_cases.py` | Cambiar `content[:200]` → `content[:500]` | `fix(search): increase preview length from 200 to 500 chars` |
| 1.2 | `tests/unit/test_search_preview_length.py` | Test que verifique preview >= 500 chars | `test(search): add preview length validation test` |
| 1.3 | `src/application/skill_hub_indexing_strategy.py` | Cambiar `content[:200]` → `content[:500]` | `fix(search): update preview length in skill hub strategy` |

**Gates de Calidad**:

- [ ] `uv run ruff check src/application/use_cases.py`
- [ ] `uv run ruff check src/application/skill_hub_indexing_strategy.py`
- [ ] `uv run pytest tests/unit/test_search_preview_length.py -v`
- [ ] `uv run mypy src/application/use_cases.py --no-error-summary`

---

### Fase 2: Search in Full Chunk Text

**Objetivo**: Cambiar búsqueda para buscar en texto completo del chunk

| Task | Archivo | Cambio | Commit |
|------|---------|--------|--------|
| 2.1 | `src/application/context_service.py` | Cambiar `for entry in pack.index` → `for chunk in pack.chunks` | `fix(search): search in full chunk text instead of truncated preview` |
| 2.2 | `tests/unit/test_search_full_text.py` | Test búsqueda en texto completo | `test(search): add full text search test` |
| 2.3 | `tests/integration/test_search_spanish_queries.py` | Test queries en español | `test(search): add Spanish query search test` |

**Gates de Calidad**:

- [ ] `uv run ruff check src/application/context_service.py`
- [ ] `uv run pytest tests/unit/test_search_full_text.py -v`
- [ ] `uv run pytest tests/integration/test_search_spanish_queries.py -v`
- [ ] `uv run mypy src/application/context_service.py --no-error-summary`

---

### Fase 3: Search Hints (Opcional)

**Objetivo**: Agregar campo `search_hints` para búsquedas rápidas

| Task | Archivo | Cambio | Commit |
|------|---------|--------|--------|
| 3.1 | `src/domain/context_models.py` | Agregar campo `search_hints` a `ContextIndexEntry` | `feat(search): add search_hints field to ContextIndexEntry` |
| 3.2 | `src/application/use_cases.py` | Extraer search_hints durante indexación | `feat(search): extract search_hints during indexing` |
| 3.3 | `tests/unit/test_search_hints.py` | Test extracción de search_hints | `test(search): add search hints extraction test` |

**Gates de Calidad**:

- [ ] `uv run ruff check src/domain/context_models.py`
- [ ] `uv run ruff check src/application/use_cases.py`
- [ ] `uv run pytest tests/unit/test_search_hints.py -v`
- [ ] `uv run mypy src/domain/context_models.py --no-error-summary`

---

## Checklist de Gates de Seguridad y Calidad

### Pre-Commit (Cada Fase)

- [ ] `uv run ruff check <archivos_modificados>`
- [ ] `uv run ruff format <archivos_modificados>`
- [ ] `uv run pytest tests/unit/ -v` (tests relacionados)
- [ ] `uv run mypy <archivos_modificados> --no-error-summary`
- [ ] Revisión de código (branch review)

### Pre-Merge (Final)

- [ ] Todos los tests pasan: `uv run pytest -v`
- [ ] Linting limpio: `uv run ruff check src/`
- [ ] Type checking limpio: `uv run mypy src/ --no-error-summary`
- [ ] Branch review aprobado
- [ ] Anchor.md actualizado con diffs
