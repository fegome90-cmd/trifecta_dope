### Blocker 1: G2 Path Hygiene (PRIORIDAD 1 — Auditabilidad)

**Hipótesis root-cause a confirmar:**
- `use_cases.py:481` llama `pack.model_dump_json()` sin sanitización
- `TrifectaPack.repo_root` se setea con `resolve_segment_root().resolve()` (absoluto)
- Templates en `templates.py` pueden interpolar paths directamente

**Herramientas de diagnóstico:**
```bash
# Localizar writer de context_pack (AP8: SSOT)
rg -n "context_pack|ContextPack|write.*pack|json.*pack" src/
# Esperado: src/application/use_cases.py:481 (AtomicWriter.write)
# Esperado: src/domain/context_models.py (TrifectaPack class)

# Localizar campos de path (AP8: SSOT)
rg -n "repo_root|source_files|path|abs|resolve\(" src/
# Esperado: repo_root en context_models.py
# Esperado: resolve() en segment_utils.py

# Verificar uso de AtomicWriter
rg -n "AtomicWriter|model_dump_json|sanitized" src/
```

**Archivos candidatos:**
- `src/domain/context_models.py` — Agregar `sanitized_dump()` method
- `src/application/use_cases.py` — Línea 481: cambiar `model_dump_json()` → `sanitized_dump()`
- `src/infrastructure/templates.py` — Verificar interpolación de paths
- `tests/unit/test_path_hygiene.py` — NUEVO: unit test
- `tests/integration/test_path_hygiene_e2e.py` — NUEVO: integration test

**Patch mínimo (descripción):**

**1. context_models.py — Agregar método sanitized_dump():**
