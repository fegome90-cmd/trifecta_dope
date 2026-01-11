### Blocker 1: G2 Path Hygiene (PRIORIDAD 1 — Auditabilidad)

**Root-cause confirmado:**
- `use_cases.py:481` escribe `pack.model_dump_json()` directamente sin sanitización
- `TrifectaPack.repo_root` contiene path absoluto desde `resolve_segment_root().resolve()`
- Templates en `templates.py` pueden incluir rutas en texto plano

**Archivos a modificar:**
- `src/domain/context_models.py` (agregar método sanitized_dump)
- `src/application/use_cases.py` (línea 481: cambiar dump por sanitized)
- `tests/unit/test_path_hygiene.py` (NUEVO: test unit + integration)

**Patch mínimo:**

**1. Agregar método en context_models.py:**
