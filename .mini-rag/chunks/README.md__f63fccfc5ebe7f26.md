#### Contenido Clave:
- **Líneas 7-18**: [Scope Map](#a-scope-map) - Features y rutas
  - ctx sync/search/get → `context_service.py`, `cli.py`
  - PD L0 Skeleton → `context_service.py:265-301`
  - PD L1 AST/LSP → `cli_ast.py`, `lsp_daemon.py`

- **Líneas 20-35**: [10 Invariantes](#b-invariantes-identificadas)
  - segment_root SSOT: `segment_utils.py:6-28`
  - segment_id = 8 chars SHA256: `segment_utils.py:31-37`
  - Schema version = 1: `context_models.py:42`
  - timing_ms >= 1: `telemetry.py:66`
  - stop_reason enum: `context_service.py:139-213`

- **Líneas 37-56**: [SSOT / Duplicaciones](#c-ssot--duplicaciones)
  - ⚠️ CORRECCIÓN: ContextPack NO está duplicado (error de reporte original)

- **Líneas 58-260**: [Evidencia Reproducible](#d-evidencia-reproducible)
  - Git SHA, status, pytest errors
  - PD L0: ctx sync/search/get (modes skeleton/excerpt/raw)
  - PD L1: ast hover/symbols outputs
  - Telemetría: 260 líneas de events.jsonl

---
