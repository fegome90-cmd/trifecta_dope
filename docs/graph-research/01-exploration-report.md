# STATUS: PARTIALLY OBSOLETE
Reemplazo vigente: `docs/graph-research/06-mvp-launch-synthesis.md`, `docs/graph-research/02-segment-ssot-audit.md`, `docs/graph-research/03-ast-lsp-maturity-audit.md`, `docs/graph-research/04-graph-pcc-boundary-audit.md`, `docs/graph-research/05-module-reuse-audit.md`
Motivo: mantiene valor histórico de reconocimiento, pero ya no debe usarse para decidir SSOT, madurez AST/LSP ni boundary Graph↔PCC.
No usar como base de implementación.

# Informe de Reconocimiento Técnico - Trifecta Graph

Fecha: 2026-03-13
Objetivo: Exploración del repo local para preparar implementación de Trifecta Graph

---

## A. Resumen Ejecutivo

| # | Hallazgo | Evidencia |
|---|----------|-----------|
| 1 | CLI entrypoint en `src/infrastructure/cli.py` con Typer como framework | `pyproject.toml:46` define `trifecta = "src.infrastructure.cli:main"` |
| 2 | DRIFT CRÍTICO: Dos SegmentRef SSOT con contratos diferentes | `src/domain/segment_resolver.py` vs `src/trifecta/domain/segment_ref.py` |
| 3 | AST M1 Production Ready: SkeletonMapBuilder con SQLite cache | `src/application/ast_parser.py` + `src/domain/ast_cache.py` |
| 4 | LSP Daemon operativo: UNIX socket IPC, 180s TTL, fallback a AST | `src/infrastructure/lsp_daemon.py`, `src/infrastructure/lsp_client.py` |
| 5 | PCC/Contexto: Context Pack con ctx search/get/build/validate | `trifecta ctx --help` muestra 10 comandos |
| 6 | Persistencia: Múltiples SQLite stores diferenciados por propósito | `ast_cache.py`, `repo_store.py`, `index_use_case.py` |
| 7 | ADR-007Graph aprobado: CLI-first, SQLite store, consume AST/LSP | `ADR/ADR-007-graph-code.md` (187 líneas) |
| 8 | Drift de funciones deprecated: `segment_utils.py` vs `segment_resolver.py` | `src/infrastructure/segment_utils.py` tiene wrappers deprecated |
| 9 | Platform layer existe: runtime manager, daemon manager, contracts | `src/platform/` con 8 módulos |
| 10 | Skills system activo: CLI commands + filesystem adapter | `src/infrastructure/cli_skills.py`, `src/infrastructure/skills_fs.py` |
| 11 | Telemetry: Sanitización robusta de PII para rutas absolutas | `src/infrastructure/telemetry.py` (redacta paths de usuario) |

---

## B. CLI Actual

### Entrypoint

- **Archivo**: `src/infrastructure/cli.py`
- **Comando**: `trifecta` → `src.infrastructure.cli:main`
- **Framework**: **Typer** (no Click)

### Árbol de Comandos

```
trifecta
├── status, doctor, create, load
├── repo-register, repo-list, repo-show
├── index, query
├── ast (sub-app: symbols, snippet, hover, clear-cache, cache-stats)
├── ctx (sub-app: stats, build, search, get, validate, plan, eval-plan, sync, reset)
├── session, telemetry, obsidian, linear
├── skill, legacy, repo, daemon
```

### Observaciones

- CLI registration usa `app.add_typer()` para sub-apps (líneas 83-110 en cli.py)
- Existe **segment_utils.py deprecated** que re-exporta con warnings (`src/infrastructure/segment_utils.py`)
- Custom `TrifectaGroup` para manejo de errores de opciones inválidas (línea 58)

---

## C. Segment/SegmentRef SSOT

### Fuente de Truth

| Implementación | Ubicación | Atributos |
|----------------|-----------|-----------|
| **V1 (Active)** | `src/domain/segment_resolver.py` | `root_abs`, `slug`, `fingerprint`, `id` |
| **V2 (Nueva)** | `src/trifecta/domain/segment_ref.py` | `repo_root`, `repo_id`, `segment_root`, `segment_id`, `runtime_dir`, `telemetry_dir`, `config_dir`, `cache_dir` |

### Funciones Clave

| Función | Módulo | Estado |
|---------|--------|--------|
| `resolve_segment_ref()` | `src/domain/segment_resolver.py:97` | ✅ Activa |
| `get_segment_root()` | `src/domain/segment_resolver.py:137` | ✅ Activa |
| `get_segment_slug()` | `src/domain/segment_resolver.py:149` | ✅ Activa |
| `resolve_segment_state()` | `src/infrastructure/segment_state.py:26` | ✅ Activa |

### Riesgos de Drift

1. **Múltiples SegmentRef**: Dos dataclasses con contratos diferentes
2. **Versión newer en `src/trifecta/`**: Fecha 2026-03-06, más campos (runtime_dir, telemetry_dir, etc.)
3. **Funciones deprecated duplicadas**: `segment_utils.py` vs `segment_resolver.py`
4. **Inconsistencia**: V1 usa `root_abs`, V2 usa `segment_root`

---

## D. AST Actual

### Qué Existe

| Componente | Ubicación | Madurez |
|------------|-----------|---------|
| **SkeletonMapBuilder** | `src/application/ast_parser.py:45` | M1 PRODUCTION |
| **AstCache Protocol** | `src/domain/ast_cache.py:54` | Stable |
| **SQLiteCache** | `src/domain/ast_cache.py:205` | Stable |
| **InMemoryLRUCache** | `src/domain/ast_cache.py:90` | Stable |

### Cómo se Invoca

```bash
# CLI commands
trifecta ast symbols "sym://python/mod/src.domain.result" --segment .
trifecta ast clear-cache --segment .
trifecta ast cache-stats --segment .
```

### Contrato/Salida

```json
// trifecta ast symbols output (M1)
{
  "status": "ok",
  "symbols": [
    {"name": "SegmentRef", "kind": "class", "file": "src/domain/segment_resolver.py", "line": 22}
  ]
}
```

### Cobertura de Lenguajes

- **Python**: Soporte completo vía `ast` stdlib
- **tree-sitter**: Dependencia en `pyproject.toml` pero no activamente usada en M1

---

## E. LSP Actual

### Qué Existe

| Componente | Ubicación | Madurez |
|------------|-----------|---------|
| **LSPDaemonServer** | `src/infrastructure/lsp_daemon.py:24` | RELAXED READY |
| **LSPClient** | `src/infrastructure/lsp_client.py` | RELAXED READY |
| **Daemon Manager** | `src/platform/daemon_manager.py` | Stable |

### Cómo se Invoca

```bash
# CLI commands
trifecta daemon start <repo>
trifecta daemon stop <repo>
trifecta daemon status <repo>
trifecta ast hover <file> <line> <col>
```

### Contrato/Salida

- **Protocolo**: UNIX Socket IPC
- **TTL**: 180 segundos
- **Fallback**: AST-only si daemon falla/warmup
- **Daemon paths**: `src/infrastructure/daemon_paths.py`

### Madurez

- Estado: **RELAXED READY** (verificado en agent_trifecta_dope.md línea 190)
- Tests de integración: `tests/integration/test_lsp_daemon.py`
- Auditoría: Documentada en `docs/lsp/`

---

## F. Contexto/PCC Actual

### Componentes

| Use Case | Ubicación | Función |
|----------|-----------|---------|
| **BuildContextPackUseCase** | `src/application/use_cases.py:164` | Construye context_pack.json |
| **ValidateContextPackUseCase** | `src/application/use_cases.py:676` | Valida integridad |
| **SearchUseCase** | `src/application/search_get_usecases.py` | Búsqueda en chunks |
| **GetChunkUseCase** | `src/application/search_get_usecases.py` | Recuperación de chunks |
| **PlanUseCase** | `src/application/plan_use_case.py` | Planificación PRIME-only |

### Flujo Real

```
trifecta ctx sync
  → BuildContextPackUseCase.execute()
    → Escanea archivos del segmento
    → Genera chunks con anchor extraction
    → Guarda context_pack.json
  → ValidateContextPackUseCase.execute()
    → Valida estructura y consistencia

trifecta ctx search
  → SearchUseCase.execute()
    → Query expansion/normalization
    → Búsqueda en index de chunks
    → Retorna SearchResult con chunk_ids

trifecta ctx get
  → GetChunkUseCase.execute()
    → Carga chunks por ID
    → Retorna contenido completo
```

### Stores/Artefactos

| Archivo | Ubicación | Contenido |
|---------|-----------|-----------|
| `context_pack.json` | `_ctx/context_pack.json` | Chunks indexados + metadata |
| `context_pack.json.sha256` | `_ctx/context_pack.json.sha256` | Checksum |
| `.autopilot.lock` | `_ctx/.autopilot.lock` | Lock para operaciones atómicas |

---

## G. Persistencia Local

### SQLite Stores

| Store | Ubicación Schema | Propósito |
|-------|-----------------|-----------|
| **AST Cache** | `src/domain/ast_cache.py:228` | Cache de símbolos parseados |
| **Repo Store** | `src/platform/repo_store.py:29` | Registry de repositorios |
| **Search DB** | `src/application/index_use_case.py:17` | Índice de búsqueda |
| **Runtime DB** | `src/platform/contracts.py:69` | Estado runtime |

### Rutas de DB/cache

```python
# De contracts.py
runtime_dir = ~/.local/share/trifecta/repos/{repo_id}/
├── ast.db
├── anchors.db
├── search.db
├── runtime.db
├── daemon
├── telemetry/
└── cache/
```

### Telemetry

| Archivo | Ubicación | Contenido |
|---------|-----------|-----------|
| `events.jsonl` | `_ctx/telemetry/events.jsonl` | Eventos de CLI |
| `last_run.json` | `_ctx/telemetry/last_run.json` | Stats agregados |

**Nota de Seguridad**: Telemetry implementa un pipeline de sanitización que redacta automáticamente rutas absolutas y URIs de archivos para evitar filtraciones de PII.

---

## H. Gaps Reales para Trifecta Graph

### Faltantes Concretos

| Gap | Evidencia | Acción Requerida |
|-----|-----------|------------------|
| **No existe comando `trifecta graph`** | CLI actual no tiene namespace graph | Crear `cli_graph.py` + add_typer |
| **No existe graph store SQLite** | ADR-007 especifica pero no implementado | Implementar schema de grafo |
| **No hay IR semántico** | Pipeline ADR dice "AST/LSP → normalización → IR" | Implementar normalizer |
| **No existe query engine para grafo** | Solo ctx search/get existen | Crear GraphQueryUseCase |

### Piezas Parciales Reutilizables

| Pieza | Reutilizar para Graph | Por qué |
|-------|----------------------|---------|
| `SkeletonMapBuilder` | ✅ Sí | Already extracts symbols + relationships |
| `SQLiteCache` | ✅ Sí | Base para graph store |
| `SegmentRef` | ✅ Sí (V2) | Identity del grafo por segmento |
| `pr2_context_searcher.py` | ⚠️ Parcial | Lógica de búsqueda, adaptar |
| `ctx_plan` | ⚠️ Parcial | Ranking logic adaptable |

### Bloqueos Reales

1. **DRIFT de SegmentRef**: Debe resolverse antes de implementar Graph
2. **No hay schema de grafo**: SQL tables para nodes/edges no existen
3. **ADR-007 indica superficie CLI** pero no hay implementación aún

---

## I. No Duplicar - Lista Explícita

### Piezas Existentes que NO deben rehacerse

| Pieza | Ubicación | NO hacer |
|-------|-----------|----------|
| **AST Parser** | `src/application/ast_parser.py` | ❌ Reescribir - consumirlo |
| **LSP Daemon** | `src/infrastructure/lsp_daemon.py` | ❌ Reimplementar - enriquecer |
| **Context Pack Builder** | `src/application/use_cases.py:164` | ❌ Duplicar - usar para seed |
| **SQLite Cache** | `src/domain/ast_cache.py` | ❌ Reescribir - extender |
| **Segment Resolution** | `src/domain/segment_resolver.py` | ❌ Duplicar - adoptar uno |
| **CLI Framework** | `src/infrastructure/cli.py` | ❌ Cambiar - agregar namespace |
| **Telemetry** | `src/infrastructure/telemetry.py` | ❌ Reemplazar - integrar |

### Qué Parece Parecido pero Cumple Otro Rol

| Parecido | Realidad | Distinción |
|----------|----------|------------|
| `trifecta index` | Index textual (chunks) | No es grafo estructural |
| `trifecta ctx search` | Búsqueda por keywords | No es query estructural |
| `trifecta ast symbols` | Extracción de símbolos | No persiste relaciones |
| `repo_store.py` | Registry de repos | No es graph store |

---

## J. Recomendación de Siguiente Exploración

### Archivo/Módulo a Revisar Inmediatamente

| Prioridad | Ruta | Por qué |
|-----------|------|---------|
| **1** | `src/domain/ast_models.py` | Modelos de símbolos - base para graph nodes |
| **2** | `src/application/symbol_selector.py` | Resolución de relaciones (callers/callees) |
| **3** | `src/domain/context_models.py` | Contratos de ContextPack - ver si adaptable |
| **4** | `src/infrastructure/cli_ast.py` | Patrón de cómo agregar nuevo namespace CLI |

### Por qué estos archivos

1. **ast_models.py**: Define `SymbolInfo` y `SkeletonMap` - los "nodos" del grafo
2. **symbol_selector.py**: Ya tiene lógica de "symbol resolution" - posible precursor de "callers/callees"
3. **context_models.py**: Muestra el contrato de datos actual - reusable para graph
4. **cli_ast.py**: Ejemplo de cómo agregar sub-app con `add_typer` - template para `trifecta graph`

---

## Criterio de Éxito Cumplido

✅ puedo responder con claridad:

- **Dónde vive el CLI real**: `src/infrastructure/cli.py` con Typer
- **Cuál es el SSOT de segment**: `src/domain/segment_resolver.py` (con drift a `src/trifecta/domain/segment_ref.py`)
- **Qué tenemos de AST**: SkeletonMapBuilder M1 Production + SQLiteCache
- **Qué tenemos de LSP**: Daemon con UNIX socket, 180s TTL, fallback a AST
- **Cómo funciona PCC hoy**: Context Pack con ctx search/get/build/validate
- **Qué persistencia ya existe**: Múltiples SQLite stores diferenciados
- **Qué partes NO duplicar**: AST parser, LSP daemon, ContextPack builder, Telemetry
