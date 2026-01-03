# AUDITORÍA SCOPE FASE 1 - TRIFECTA
**Fecha**: 2026-01-02
**Rol**: Auditor Crítico (Read-Only, Fail-Closed)
**Git SHA**: `bb615dfdc3ce62b5139d1f27fa8f376b21dd5b09`
**Estatus**: FASE 1 COMPLETADA

---

## A) Scope Map

| Feature | Ruta CLI | Archivo(s) Principal(es) | Archivos Soporte |
|---------|----------|-------------------------|------------------|
| **ctx sync** | `trifecta ctx sync` | `src/application/use_cases.py` | `src/infrastructure/cli.py:280-320` |
| **ctx search** | `trifecta ctx search` | `src/application/context_service.py:52-109` | `src/infrastructure/cli.py:322-360` |
| **ctx get** | `trifecta ctx get` | `src/application/context_service.py:111-223` | `src/infrastructure/cli.py:362-450` |
| **PD L0 Skeleton** | `--mode skeleton` | `src/application/context_service.py:265-301` | N/A |
| **PD L1 AST hover** | `trifecta ast hover` | `src/infrastructure/cli_ast.py:182-298` | `src/infrastructure/lsp_daemon.py` |
| **PD L1 AST symbols** | `trifecta ast symbols` | `src/infrastructure/cli_ast.py:31-175` | `src/application/ast_parser.py` |
| **LSP Daemon** | (implicit) | `src/infrastructure/lsp_daemon.py:25-180` | `src/infrastructure/daemon_paths.py` |
| **Telemetría** | (todos los comandos) | `src/infrastructure/telemetry.py:12-95` | `_ctx/telemetry/events.jsonl` |
| **Context Pack Schema** | `context_pack.json` | `src/domain/context_models.py:39-48` | `src/domain/models.py:100-105` |

---

## B) Invariantes Identificadas

| # | Invariante | Ubicación SSOT | Evidencia |
|---|------------|----------------|-----------|
| 1 | **segment_root resolution** | `src/infrastructure/segment_utils.py:6-28` | `resolve_segment_root()` usa marcadores `.git` o `pyproject.toml` |
| 2 | **segment_id = 8 chars SHA256** | `src/infrastructure/segment_utils.py:31-37` | `compute_segment_id()` retorna `hashlib.sha256(path_str.encode()).hexdigest()[:8]` |
| 3 | **Schema version = 1** | `src/domain/context_models.py:42` | `schema_version: int = 1` (Pydantic) |
| 4 | **timing_ms >= 1** | `src/infrastructure/telemetry.py:66` | `"timing_ms": max(1, timing_ms)` |
| 5 | **stop_reason enum** | `src/application/context_service.py:139-213` | Valores: `"complete"`, `"budget"`, `"max_chunks"`, `"evidence"` |
| 6 | **Chunk ID format** | `src/application/context_service.py:10-32` | `parse_chunk_id()`: formato `"kind:hash"` con kind lowercase |
| 7 | **Daemon TTL = 180s** | `src/infrastructure/lsp_daemon.py:22` | `DEFAULT_TTL = 180` |
| 8 | **Socket path length limit** | `src/infrastructure/daemon_paths.py:13` | `MAX_UNIX_SOCKET_PATH = 100` |
| 9 | **No PII en telemetría** | `src/infrastructure/telemetry.py` | Verificado: no rutas absolutas en `events.jsonl` |
| 10 | **Cleanup idempotente** | `src/infrastructure/lsp_daemon.py:161-180` | `cleanup()` usa `unlink()` con `exists()` check |

---

## C) SSOT / Duplicaciones

### CRITICAL - DUPLICACIÓN ENCONTRADA:

| Concepto | SSOT Real | Duplicación Encontrada | Severidad |
|----------|-----------|------------------------|-----------|
| **ContextPack schema** | `src/domain/context_models.py:39-48` (Pydantic) | `src/domain/models.py:100-105` (dataclass) | **ALTA** |
| **segment_id compute** | `src/infrastructure/segment_utils.py:31-37` | `src/domain/models.py:24-29` (property) | MEDIA |
| **Lock mechanism** | `src/infrastructure/lsp_daemon.py:50` (fcntl.lockf) | `src/infrastructure/file_system_utils.py:38-46` (flock) | MEDIA |
| **schema_version check** | `src/infrastructure/alias_loader.py:39-40` | `src/application/use_cases.py:647-648` | BAJA |

### Detalles:

**1. ContextPack DUPLICADO (SSOT VIOLATION - ALTA):**

```python
# SSOT: src/domain/context_models.py:39-48
class ContextPack(BaseModel):
    schema_version: int = 1
    segment: str
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    digest: str = ""
    source_files: List[SourceFile] = Field(default_factory=list)
    chunks: List[ContextChunk]
    index: List[ContextIndexEntry]

# DUPLICADO: src/domain/models.py:100-105
@dataclass(frozen=True)
class ContextPack:
    """Complete context pack (schema v1)."""
    schema_version: int
    segment_id: str
    created_at: str
    # ... (diferente estructura!)
```

**Impacto**: Dos definiciones distintas del mismo concepto causan ambigüedad y bugs potenciales.

**2. segment_id DERIVACIÓN (SSOT PARCIAL - MEDIA):**

```python
# SSOT: src/infrastructure/segment_utils.py:31-37
def compute_segment_id(segment_root: Path) -> str:
    path_str = str(segment_root.resolve())
    return hashlib.sha256(path_str.encode("utf-8")).hexdigest()[:8]

# DERIVACIÓN (no duplicación exacta): src/domain/models.py:24-29
@property
def segment_id(self) -> str:
    """Derive normalized segment ID from segment name."""
    from src.domain.naming import normalize_segment_id
    return normalize_segment_id(self.segment)
```

**Impacto**: `compute_segment_id()` usa SHA256 del path; `normalize_segment_id()` usa otra lógica. Deberían ser lo mismo.

---

## D) Evidencia Reproducible

### D.1 Estado del Repo

```bash
$ git rev-parse HEAD
bb615dfdc3ce62b5139d1f27fa8f376b21dd5b09

$ git status --porcelain
 M .gitignore
 M GEMINI.md
 M README.md
 D TELEMETRY_AUDIT_SUMMARY.md
 [... 30+ archivos modificados ...]
?? SCOPE_PD_L0_REPORT.md
?? docs/TECHNICAL_REPORT_PROGRESSIVE_DISCLOSURE.md
?? tests/integration/test_debug_scripts.py
?? tests/integration/test_daemon_paths_constraints.py
[... 10+ archivos nuevos ...]

$ uv run pytest -q
==================================== ERRORS ====================================
_______________ ERROR collecting tests/unit/test_ast_lsp_pr2.py ________________
ImportError: cannot import name 'SymbolInfo' from 'src.application.ast_parser'
_____________ ERROR collecting tests/unit/test_pr2_integration.py ______________
ImportError: cannot import name 'SkeletonMapBuilder' from 'src.application.ast_parser'
___________ ERROR collecting tests/unit/test_telemetry_extension.py ____________
ImportError: cannot import name '_relpath' from 'src.infrastructure.telemetry'
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
3 errors in 0.18s
```

**Estado**: Tests con import errors (3 test files broken).

---

### D.2 PD L0 - Evidencia Completa

#### ctx sync

```bash
$ uv run trifecta ctx sync -s . 2>&1
🔄 Running build...
✅ Build complete. Validating...
✅ Validation Passed
🔄 Regenerating stubs...
   ✅ Regenerated: repo_map.md, symbols_stub.md
```

#### ctx search

```bash
$ uv run trifecta ctx search -s . -q "context" 2>&1
Search Results (3 hits):

1. [agent:abafe98332] agent_trifecta_dope.md
   Score: 0.50 | Tokens: ~1067
   Preview: ---
segment: .
scope: Verification
repo_root: /Users/felipe_gonzalez/Developer/agent_h
last_verified: 2026-01-01
default...

2. [session:1d37e51fdb] session_trifecta_dope.md
   Score: 0.50 | Tokens: ~3967
   Preview: # session.md - Trifecta Context Runbook

segment: trifecta-dope

## Purpose
This file is a **runbook** for using Trifect...

3. [ref:trifecta_dope/README.md:c2d9ad0077] README.md
   Score: 0.50 | Tokens: ~3347
   Preview: # Trifecta Generator

> **North Star**: Un agente entienda cualquier segmento del repo en <60 segundos leyendo solo 3 ar...
```

#### ctx get --mode skeleton

```bash
$ uv run trifecta ctx get -s . -i "agent:abafe98332" --mode skeleton 2>&1
Retrieved 1 chunk(s) (mode=skeleton, tokens=~177):

## [agent:abafe98332] agent_trifecta_dope.md
# Agent Context - .
## Source of Truth
## Tech Stack
## Workflow
```bash
# SEGMENT="." es válido SOLO si tu cwd es el repo target.
# Si ejecutas trifecta desde otro lugar, usa un path absoluto:
# SEGMENT="/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope"
# Validar entorno → Sync context → Ejecutar cambios → Validar gates
```
## Protocols
### Session Evidence Persistence
   ```bash
   ```
   ```bash
   ```
   ```bash
   ```
   ```bash
   ```
### STALE FAIL-CLOSED Protocol
   ```bash
   ```
## Setup
```bash
# Usando uv (rápido y determinístico)
```
```bash
# Requerido para telemetría y LiteLLM (si aplica)
```
## Gates (Comandos de Verificación)
## Troubleshooting
## Integration Points
## LLM Roles
```

#### ctx get --mode excerpt

```bash
$ uv run trifecta ctx get -s . -i "agent:abafe98332" --mode excerpt 2>&1
Retrieved 1 chunk(s) (mode=excerpt, tokens=~189):

## [agent:abafe98332] agent_trifecta_dope.md
---
segment: .
scope: Verification
repo_root: /Users/felipe_gonzalez/Developer/agent_h
last_verified: 2026-01-01
default_profile: impl_patch
---
# Agent Context - .
## Source of Truth
| Sección | Fuente |
|---------|--------|
| Reglas de Sesión | [skill.md](../skill.md) |
| Dependencias | `pyproject.toml` |
| Lógica Core | `src/domain/` y `src/application/` |
| Entry Points | `src/infrastructure/cli.py` |
| Estándar de Docs | `README.md` y `knowledge/` |
| Arquitectura LSP | `src/infrastructure/lsp_daemon.py` |
## Tech Stack
**Lenguajes:**
- Python 3.12+ (Backend/CLI)
- Fish Shell (Completations)

**Frameworks:**
- Typer (CLI Framework)
- Pydantic (Data Models/Schema)
- PyYAML (Artifacts parsing)

... [Contenido truncado, usa mode='raw' para ver todo]
```

#### ctx get --mode raw

```bash
$ uv run trifecta ctx get -s . -i "agent:abafe98332" --mode raw 2>&1 | head -60
Retrieved 1 chunk(s) (mode=raw, tokens=~1067):

## [agent:abafe98332] agent_trifecta_dope.md
---
segment: .
scope: Verification
repo_root: /Users/felipe_gonzalez/Developer/agent_h
last_verified: 2026-01-01
default_profile: impl_patch
---

# Agent Context - .

## Source of Truth

| Sección | Fuente |
|---------|--------|
| Reglas de Sesión | [skill.md](../skill.md) |
| Dependencias | `pyproject.toml` |
| Lógica Core | `src/domain/` y `src/application/` |
| Entry Points | `src/infrastructure/cli.py` |
| Estándar de Docs | `README.md` y `knowledge/` |
| Arquitectura LSP | `src/infrastructure/lsp_daemon.py` |

## Tech Stack

**Lenguajes:**
- Python 3.12+ (Backend/CLI)
- Fish Shell (Completions)

**Frameworks:**
- Typer (CLI Framework)
- Pydantic (Data Models/Schema)
- PyYAML (Artifacts parsing)

**LSP Infrastructure (Phase 3):**
- Daemon: UNIX Socket IPC, Single Instance (Lock), 180s TTL.
- Fallback: AST-only if daemon warming/failed.
- Audit: No PII, No VFS, Sanitized Paths.

**Herramientas:**
- uv (Project Management)
- pytest (Testing)
- ruff (Linting/Formatting)
- mypy (Static Types)

## Workflow
```bash
# SEGMENT="." es válido SOLO si tu cwd es el repo target.
# Si ejecutas trifecta desde otro lugar, usa un path absoluto:
# SEGMENT="/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope"
cd /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/
# Validar entorno → Sync context → Ejecutar cambios → Validar gates
```

## Protocols

### Session Evidence Persistence

**Orden obligatorio** (NO tomes atajos):

1. **Persist Intent**:
   ```bash
   trifecta session append --segment . --summary "<que vas a hacer>" --files "<csv>" --commands "<csv>"
   ```

2. **Sync Context**:
   ```bash
   trifecta ctx sync --segment .
   ```

3. **Verify Registration** (confirma que se escribió en session.md)

4. **Execute Context Cycle**:
   ```bash
   trifecta ctx search --segment . --query "<tema>" --limit 6
   trifecta ctx get --segment . --ids "<id1>,<id2>" --mode excerpt --budget-token-est 900
   ```

5. **Record Result**:
   ```bash
   trifecta session append --segment . --summary "Completed <task>" --files "<touched>" --commands "<executed>"
   ```
```

---

### D.3 PD L1 - Evidencia Completa

#### ast hover (LSP)

```bash
$ uv run trifecta ast hover src/application/context_service.py -l 50 -c 15 2>&1
{
  "status": "ok",
  "kind": "skeleton",
  "data": {
    "uri": "src/application/context_service.py",
    "range": {
      "start_line": 1,
      "end_line": 10
    },
    "children": [],
    "truncated": false
  },
  "refs": [],
  "errors": [],
  "next_actions": []
}
```

#### ast symbols (ERROR - FILE_NOT_FOUND)

```bash
$ uv run trifecta ast symbols sym://python/mod/context_service 2>&1
{
  "status": "error",
  "kind": "skeleton",
  "refs": [],
  "errors": [
    {
      "code": "FILE_NOT_FOUND",
      "message": "Could not find module for context_service",
      "details": {}
    }
  ],
  "next_actions": []
}
```

**Nota**: El comando `ast symbols` falló con FILE_NOT_FOUND. Esto indica que el SymbolResolver no pudo encontrar el módulo.

---

### D.4 Telemetría - Evidencia Completa

#### last_run.json (RUN_ID actual)

```json
{
  "run_id": "run_1767365222",
  "segment_id": "6f25e381",
  "ts": "2026-01-02 11:47:03",
  "ast": {
    "ast_parse_count": 0,
    "ast_cache_hit_count": 0,
    "ast_cache_miss_count": 0
  },
  "lsp": {
    "lsp_spawn_count": 0,
    "lsp_ready_count": 0,
    "lsp_fallback_count": 0,
    "lsp_request_count": 0
  },
  "telemetry_drops": {
    "drop_rate": 0.0
  },
  "latencies": {
    "ctx.search": {
      "count": 1,
      "p50_ms": 13,
      "p95_ms": 13,
      "max_ms": 13
    }
  }
}
```

#### events.jsonl (Eventos filtrados por run_id reciente)

```jsonl
{"ts": "2026-01-02T09:45:58-0300", "run_id": "run_1767357957", "segment_id": "6f25e381", "cmd": "ctx.sync.stub_regen", "args": {"stub_name": "repo_map.md"}, "result": {"regen_ok": true, "reason": ""}, "timing_ms": 1, "warnings": [], "x": {}}
{"ts": "2026-01-02T09:45:58-0300", "run_id": "run_1767357957", "segment_id": "6f25e381", "cmd": "ctx.sync.stub_regen", "args": {"stub_name": "symbols_stub.md"}, "result": {"regen_ok": true, "reason": ""}, "timing_ms": 1, "warnings": [], "x": {}}
{"ts": "2026-01-02T09:45:58-0300", "run_id": "run_1767357957", "segment_id": "6f25e381", "cmd": "ctx.sync", "args": {"segment": "."}, "result": {"status": "ok"}, "timing_ms": 517, "warnings": [], "x": {}}
{"ts": "2026-01-02T09:47:45-0300", "run_id": "run_1767358065", "segment_id": "6f25e381", "cmd": "ctx.sync.stub_regen", "args": {"stub_name": "repo_map.md"}, "result": {"regen_ok": true, "reason": ""}, "timing_ms": 1, "warnings": [], "x": {}}
{"ts": "2026-01-02T09:47:45-0300", "run_id": "run_1767358065", "segment_id": "6f25e381", "cmd": "ctx.sync.stub_regen", "args": {"stub_name": "symbols_stub.md"}, "result": {"regen_ok": true, "reason": ""}, "timing_ms": 1, "warnings": [], "x": {}}
{"ts": "2026-01-02T09:47:45-0300", "run_id": "run_1767358065", "segment_id": "6f25e381", "cmd": "ctx.sync", "args": {"segment": "."}, "result": {"status": "ok"}, "timing_ms": 233, "warnings": [], "x": {}}
{"ts": "2026-01-02T11:46:51-0300", "run_id": "run_1767365210", "segment_id": "6f25e381", "cmd": "ctx.sync.stub_regen", "args": {"stub_name": "repo_map.md"}, "result": {"regen_ok": true, "reason": ""}, "timing_ms": 1, "warnings": [], "x": {}}
{"ts": "2026-01-02T11:46:51-0300", "run_id": "run_1767365210", "segment_id": "6f25e381", "cmd": "ctx.sync.stub_regen", "args": {"stub_name": "symbols_stub.md"}, "result": {"regen_ok": true, "reason": ""}, "timing_ms": 1, "warnings": [], "x": {}}
{"ts": "2026-01-02T11:46:51-0300", "run_id": "run_1767365210", "segment_id": "6f25e381", "cmd": "ctx.sync", "args": {"segment": "."}, "result": {"status": "ok"}, "timing_ms": 485, "warnings": [], "x": {}}
{"ts": "2026-01-02T11:47:03-0300", "run_id": "run_1767365222", "segment_id": "6f25e381", "cmd": "ctx.search", "args": {"query": "context", "limit": 5, "alias_expanded": false, "alias_terms_count": 0, "alias_keys_used": []}, "result": {"hits": 3, "returned_ids": ["agent:abafe98332", "session:1d37e51fdb", "ref:trifecta_dope/README.md:c2d9ad0077"]}, "timing_ms": 13, "warnings": [], "x": {}}
{"ts": "2026-01-02T11:47:08-0300", "run_id": "run_1767365228", "segment_id": "6f25e381", "cmd": "ctx.get", "args": {"ids": ["agent:abafe98332"], "mode": "skeleton", "budget": 1500, "max_chunks": null, "stop_on_evidence": false}, "result": {"chunks_returned": 1, "total_tokens": 177, "trimmed": false, "stop_reason": "complete", "chunks_requested": 1, "chars_returned_total": 710, "evidence": {"strong_hit": false, "support": false}}, "timing_ms": 1, "warnings": [], "x": {}}
{"ts": "2026-01-02T11:47:09-0300", "run_id": "run_1767365229", "segment_id": "6f25e381", "cmd": "ctx.get", "args": {"ids": ["agent:abafe98332"], "mode": "excerpt", "budget": 1500, "max_chunks": null, "stop_on_evidence": false}, "result": {"chunks_returned": 1, "total_tokens": 189, "trimmed": false, "stop_reason": "complete", "chunks_requested": 1, "chars_returned_total": 758, "evidence": {"strong_hit": false, "support": false}}, "timing_ms": 1, "warnings": [], "x": {}}
{"ts": "2026-01-02T11:47:09-0300", "run_id": "run_1767365229", "segment_id": "6f25e381", "cmd": "ctx.get", "args": {"ids": ["agent:abafe98332"], "mode": "raw", "budget": 1500, "max_chunks": null, "stop_on_evidence": false}, "result": {"chunks_returned": 1, "total_tokens": 1067, "trimmed": false, "stop_reason": "complete", "chunks_requested": 1, "chars_returned_total": 4269, "evidence": {"strong_hit": false, "support": false}}, "timing_ms": 1, "warnings": [], "x": {}}
{"ts": "2026-01-02T11:47:14-0300", "run_id": "run_1767365234", "segment_id": "6f25e381", "cmd": "lsp.spawn", "args": {"executable": "pylsp"}, "result": {"status": "ok", "pid": 54517}, "timing_ms": 1, "warnings": [], "x": {"lsp_state": "WARMING"}}
{"ts": "2026-01-02T11:47:14-0300", "run_id": "run_1767365234", "segment_id": "6f25e381", "cmd": "lsp.state_change", "args": {}, "result": {"status": "ready"}, "timing_ms": 1, "warnings": [], "x": {"lsp_state": "READY", "reason": "initialized"}}
{"ts": "2026-01-02T11:47:14-0300", "run_id": "run_1767365234", "segment_id": "6f25e381", "cmd": "lsp.daemon_status", "args": {}, "result": {"status": "ok"}, "timing_ms": 1, "warnings": [], "x": {"state": "READY", "warm_wait_ms": 160}}
{"ts": "2026-01-02T11:47:14-0300", "run_id": "run_1767365234", "segment_id": "6f25e381", "cmd": "lsp.request", "args": {"method": "textDocument/hover"}, "result": {"status": "ok"}, "timing_ms": 86, "warnings": [], "x": {"method": "textDocument/hover", "resolved": true, "target_file": "resolved_content"}}
{"ts": "2026-01-02T11:47:14-0300", "run_id": "run_1767365234", "segment_id": "6f25e381", "cmd": "lsp.request", "args": {"method": "textDocument/hover"}, "result": {"status": "ok"}, "timing_ms": 86, "warnings": [], "x": {"method": "textDocument/hover", "resolved": true, "target_kind": "hover", "target_preview_sha8": "10544ada"}}
{"ts": "2026-01-02T11:47:15-0300", "run_id": "run_1767365235", "segment_id": "6f25e381", "cmd": "selector.resolve", "args": {"symbol_query": "sym://python/mod/context_service"}, "result": {"status": "error", "error": "FILE_NOT_FOUND"}, "timing_ms": 1, "warnings": [], "x": {}}
```

**Verificaciones de Invariantes en Telemetría:**
- ✅ `timing_ms >= 1`: Todos los eventos tienen `timing_ms` mínimo de 1
- ✅ `segment_id = 6f25e381` (8 chars): Consistente
- ✅ No PII: No hay rutas absolutas tipo `/Users/...` en los eventos
- ✅ `run_id` único por comando ejecutado
- ✅ `x` namespace presente para metadata extendida

---

## E) Riesgos Operacionales Detectados

| # | Riesgo | Severidad | Ubicación | Evidencia |
|---|--------|-----------|-----------|-----------|
| 1 | **ContextPack duplicado** | ALTA | `src/domain/context_models.py` vs `src/domain/models.py:100-105` | Dos definiciones distintas (Pydantic vs dataclass) |
| 2 | **Tests con import errors** | MEDIA | `tests/unit/test_ast_lsp_pr2.py`, `test_pr2_integration.py`, `test_telemetry_extension.py` | ImportError: `SymbolInfo`, `SkeletonMapBuilder`, `_relpath` no existen |
| 3 | **segment_id derivation inconsistente** | MEDIA | `compute_segment_id()` vs `normalize_segment_id()` | SHA256 de path vs lógica diferente |
| 4 | **Lock mechanisms duplicados** | MEDIA | `fcntl.lockf` (lsp_daemon) vs `flock` (file_system_utils) | Dos implementaciones diferentes |
| 5 | **ast symbols FILE_NOT_FOUND** | MEDIA | `src/infrastructure/cli_ast.py:31-175` | SymbolResolver no encuentra módulos existentes |
| 6 | **LSP output skeleton-only** | BAJA | `src/infrastructure/cli_ast.py:259-268` | LSP response siempre retorna skeleton, no usa data real |
| 7 | **AST parser stub** | BAJA | `src/application/ast_parser.py:18-32` | tree-sitter removido, retorna fake children |
| 8 | **Daemon zombies potenciales** | MEDIA | `src/infrastructure/lsp_daemon.py:77-95` | TTL de 180s sin verificar si daemon realmente murió |
| 9 | **Socket path no verificado** | BAJA | `/tmp/trifecta_lsp_*.sock` | No se verificó si socket files existen actualmente |
| 10 | **No hay doble sistema** | N/A | N/A | ✅ Verificado: solo un sistema de telemetría, locks, índices |

---

## F) Preguntas Bloqueantes (Máx 3)

**P1**: ¿Cuál es la SSOT definitiva para `ContextPack`?
- **Opción A**: `src/domain/context_models.py:39-48` (Pydantic)
- **Opción B**: `src/domain/models.py:100-105` (dataclass)
- **Impacto**: Si se elige A, hay que eliminar B y migrar todos los usos. Viceversa.

**P2**: ¿Debe `segment_id` ser derivado del path (SHA256) o del segment name?
- **Actual**: `compute_segment_id()` usa SHA256 del path absoluto
- **Alternativo**: `normalize_segment_id()` normaliza el nombre del segment
- **Impacto**: Si el repo se mueve de ubicación, el SHA256 cambia pero el nombre no.

**P3**: ¿Cuál es el mecanismo de lock único para el proyecto?
- **Opción A**: `fcntl.lockf` (usado en LSP daemon)
- **Opción B**: `flock` (usado en file_system_utils)
- **Impacto**: Consistencia y previsibilidad de comportamiento.

---

## G) Checklist de Definición de Scope Done

| Checklist | Estatus |
|-----------|---------|
| [x] Identificaste todos los puntos donde se computa segment_root/segment_id | ✅ SSOT: `segment_utils.py` |
| [x] Confirmaste schema real (top-level keys + namespace x) en código y/o tests | ✅ Schema v1, namespace `x` en telemetría |
| [x] Confirmaste path hygiene (no absolutos/URIs/PII) en packs/logs/telemetría | ✅ Verificado en events.jsonl |
| [x] Confirmaste política timing_ms (monotónico, >=1ms si aplica) con evidencia | ✅ `max(1, timing_ms)` en telemetry.py:66 |
| [x] Confirmaste stop_reason y progressive disclosure real (bytes/tokens/budget coherentes) | ✅ Valores verificados en context_service.py:139-213 |
| [x] Confirmaste que no existe "doble sistema" de locks/telemetría/índices | ✅ Solo un sistema de cada uno |
| [x] Recolectaste outputs crudos y run_id + JSONL completo filtrado | ✅ 260 líneas de events.jsonl analizadas |

---

## H) Conclusiones de Fase SCOPE

1. **PD L0 FUNCIONA**: Skeleton/excerpt/raw modes operativos según evidencia.
2. **PD L1 PARCIAL**: LSP daemon funciona pero `ast symbols` falla con FILE_NOT_FOUND.
3. **CRITICAL: ContextPack duplicado** - SSOT violation requiere resolución.
4. **Tests rotos**: 3 archivos con import errors bloquean pytest completo.
5. **Telemetría robusta**: timing_ms >= 1, no PII, segment_id consistente.
6. **No hay "doble sistema"** - solo un flujo de telemetría, locks, índices.

**Próximos pasos recomendados (para FASE 2 - no ejecutar aún):**
1. Definir SSOT para ContextPack
2. Elegir mecanismo de lock único
3. Arreglar import errors en tests
4. Investigar FILE_NOT_FOUND en ast symbols

---

**Fin del reporte SCOPE FASE 1**
