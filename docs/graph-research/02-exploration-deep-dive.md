# STATUS: SUPERSEDED
Reemplazo vigente: `docs/graph-research/06-mvp-launch-synthesis.md`, `docs/graph-research/02-segment-ssot-audit.md`, `docs/graph-research/03-ast-lsp-maturity-audit.md`, `docs/graph-research/04-graph-pcc-boundary-audit.md`, `docs/graph-research/05-module-reuse-audit.md`
Motivo: contiene afirmaciones invalidadas sobre V2 como SSOT, LSP "production-ready" y symbol↔chunk linking para MVP.
No usar como base de implementación.

# Informe de Exploración Técnica - Trifecta Graph (Deep Dive)

**Fecha**: 2026-03-13
**Estado**: Exploración completada
**Propósito**: Reconocimiento detallado para implementar capa Trifecta Graph (CLI-first, sin duplicar AST/LSP, respetando PCC/meta-first)

---

## A. Resumen Ejecutivo (10 hallazgos críticos)

| # | Hallazgo | Impacto |
|---|----------|---------|
| 1 | **CLI usa Typer**, entrypoint `src.infrastructure.cli:main` | Base para añadir namespace `graph` |
| 2 | **DOS SegmentRef** incompatibles | ⚠️ **CRÍTICO**: Resolver antes de implementar |
| 3 | **AST usa stdlib**, NO tree-sitter | No reconstruir parser |
| 4 | **LSP daemon production-ready** | Consumir, no duplicar |
| 5 | **SQLite cache existe** | Reutilizar patrones |
| 6 | **Telemetry PR#1 completo** | Seguir modelo |
| 7 | **Context pack único** (663 chunks) | Leer solo, no modificar |
| 8 | **Inconsistencia IDs** (path vs hash) | Unificar en `normalize_segment_id()` |
| 9 | **ADR-007 define Graph** | Blueprint listo |
| 10 | **Sin namespace `graph`** | Crear siguiendo patrón `ast` |

---

## B. CLI Actual

### B.1 Entrypoint

| Aspecto | Valor |
|---------|-------|
| **Binario** | `trifecta` |
| **Entry point** | `src.infrastructure.cli:main` |
| **Framework** | **Typer** (decoradores `@app.command`) |
| **Archivo principal** | `src/infrastructure/cli.py` (2739 líneas) |
| **Custom Group** | `TrifectaGroup` (error handling mejorado) |

### B.2 Árbol de Namespaces

```
trifecta
├── ctx          # Context packs (build, search, get, validate, sync, reset)
├── ast          # AST/LSP (symbols, snippet, hover, clear-cache, cache-stats)
├── session      # Session logging
├── telemetry    # Analytics (report, export, chart, health)
├── obsidian     # Vault integration
├── linear       # Linear sync
├── skill        # Skill metadata/keywords
├── legacy       # Burn-down commands
├── repo         # Repository registry
├── daemon       # Daemon management
└── [top-level]  # status, doctor, create, load, index, query
```

### B.3 Comandos Relevantes para Graph

| Comando | Archivo | Descripción |
|---------|---------|-------------|
| `ctx build` | `cli.py:443` | Construye context pack |
| `ctx search` | `cli.py:623` | Búsqueda con linting, alias, explain |
| `ctx get` | `cli.py:721` | Retrieval con modos (raw/excerpt/skeleton) |
| `ast symbols` | `cli_ast.py:61` | Extracción de símbolos via AST |
| `ast hover` | `cli_ast.py:196` | LSP hover con fallback |
| `ast cache-stats` | `cli_ast.py:282` | Stats del cache AST |

### B.4 Patrón de Integración

```python
# cli.py - Patrón existente para añadir namespace
app = typer.Typer(name="trifecta", cls=TrifectaGroup)

# Añadir namespace
ast_app = typer.Typer(help="AST & Parsing Commands")
app.add_typer(ast_app, name="ast")

# Para graph, seguir mismo patrón:
graph_app = typer.Typer(help="Code Graph Commands")
app.add_typer(graph_app, name="graph")
```

---

## C. Segment/SegmentRef SSOT

### C.1 PROBLEMA CRÍTICO: Duplicación

Existen **DOS** implementaciones de `SegmentRef` con contratos incompatibles.

#### SSOT Primario (trifecta/platform)

```python
# src/trifecta/domain/segment_ref.py
@dataclass(frozen=True)
class SegmentRef:
    repo_root: Path
    repo_id: str
    segment_root: Path
    segment_id: str
    runtime_dir: Path
    registry_key: str
    telemetry_dir: Path
    config_dir: Path
    cache_dir: Path
```

- **Función**: `resolve_segment_ref(segment_input: Path | str | None = None) -> SegmentRef`
- **Tests**: `tests/contracts/test_segment_ref_contract.py`
- **Estado**: **INTEGRADO**

#### SSOT Secundario (legacy/domain)

```python
# src/domain/segment_resolver.py
class SegmentRef:
    root_abs: Path
    slug: str
    fingerprint: str
    id: str  # slug_fingerprint
```

- **Función**: `resolve_segment_ref(segment_input) -> SegmentRef`
- **Estado**: **EXPERIMENTAL/DEPRECATED**

### C.2 Riesgos de Drift

1. **Contratos incompatibles**: Los 9 campos vs 4 campos rompen type hints
2. **IDs diferentes**: Path sanitizado vs SHA256 hash
3. **Imports cruzados**: Algunos módulos importan del legacy, otros del nuevo

### C.3 Recomendación

**USAR SOLO** `src/trifecta/domain/segment_ref.py`
**DEPRECAR** `src/domain/segment_resolver.py`

---

## D. AST Actual

### D.1 Componentes

| Componente | Archivo | Estado |
|------------|---------|--------|
| `SkeletonMapBuilder` | `src/application/ast_parser.py` | **PRODUCTION** |
| `AstCache` protocol | `src/domain/ast_cache.py` | **PRODUCTION** |
| `InMemoryLRUCache` | `src/domain/ast_cache.py` | **PRODUCTION** |
| `SQLiteCache` | `src/infrastructure/factories.py` | **PRODUCTION** |
| CLI `ast symbols` | `src/infrastructure/cli_ast.py:61` | **PRODUCTION** |
| CLI `ast snippet` | `src/infrastructure/cli_ast.py:170` | **NOT_IMPLEMENTED** |

### D.2 Contrato de Salida

```python
@dataclass
class ParseResult:
    symbols: List[SymbolInfo]
    status: str  # "hit" | "miss" | "error"
    cache_key: str

@dataclass
class SymbolInfo:
    name: str
    kind: str  # "function" | "class" | "method"
    line_start: int
    line_end: int
    signature: Optional[str]
```

### D.3 Invocación

```bash
# CLI
trifecta ast symbols <uri> --segment . --persist-cache

# Programático
builder = SkeletonMapBuilder(cache, segment_id)
result = builder.build(file_path)
```

### D.4 Observaciones Clave

- **NO usa tree-sitter**: Usa stdlib `ast.parse()` (Python-only)
- **Top-level only**: Solo extrae funciones/clases al nivel superior
- **Cache persistente opcional**: `TRIFECTA_AST_PERSIST=1`
- **Reutilizable para Graph**: `SkeletonMapBuilder` es base perfecta

---

## E. LSP Actual

### E.1 Componentes

| Componente | Archivo | Estado |
|------------|---------|--------|
| `LSPClient` | `src/infrastructure/lsp_client.py` | **PRODUCTION** |
| `LSPDaemonServer` | `src/infrastructure/lsp_daemon.py` | **PRODUCTION** |
| `LSPDaemonClient` | `src/infrastructure/lsp_daemon.py` | **PRODUCTION** |
| `LSPManager` | `src/application/lsp_manager.py` | **WIP/NO USADO** |
| Contratos | `src/domain/lsp_contracts.py` | **PRODUCTION** |

### E.2 Contrato de Salida

```python
@dataclass
class LSPResponse:
    status: str
    capability_state: str  # FULL | DEGRADED | WIP | UNAVAILABLE
    backend: str  # lsp_pyright | lsp_pylsp | ast_only | wip_stub
    response_state: str
    fallback_reason: Optional[str]
    data: Optional[Dict[str, Any]]
    error_code: Optional[str]
    message: Optional[str]
```

### E.3 Daemon IPC

| Aspecto | Valor |
|---------|-------|
| **Socket** | `/tmp/trifecta_lsp_{segment_id}.sock` |
| **Lock** | `/tmp/trifecta_lsp_{segment_id}.lock` |
| **PID** | `/tmp/trifecta_lsp_{segment_id}.pid` |
| **TTL** | 180s default |
| **Env** | `LSP_DAEMON_TTL_SEC` |

### E.4 Invocación

```bash
# Daemon
python -m src.infrastructure.lsp_daemon start --root <path>

# CLI
trifecta ast hover <uri> --line N --char M [--require-lsp]
```

### E.5 Observaciones Clave

- **Fallback explícito**: Retorna `LSPResponse` con `fallback_reason`, nunca silent
- **LSPManager no se usa**: Stub para pyright --outputjson
- **CLI hover es stub**: Solo detecta disponibilidad
- **Reutilizable para Graph**: `LSPDaemonClient` puede enriquecer relaciones

---

## F. Contexto/PCC Actual

### F.1 Componentes

| Componente | Archivo | Propósito |
|------------|---------|-----------|
| `ContextPack` | `src/domain/context_models.py` | Modelo Pydantic |
| `BuildContextPackUseCase` | `src/application/use_cases.py` | Construcción |
| `ContextService` | `src/application/context_service.py` | Search/Get |
| `SearchUseCase` | `src/application/search_use_case.py` | Pipeline búsqueda |

### F.2 Flujo Real

```
1. BUILD
   target_path/ → BuildContextPackUseCase.execute() → _ctx/context_pack.json

2. SEARCH
   query → Normalize → Lint (opcional) → Alias Expand → Weighted Search → SearchResult

3. GET
   ids → ContextService.get(mode, budget) → Progressive Disclosure → GetResult
```

### F.3 Stores/Artefactos

| Artefacto | Ruta | Tamaño |
|-----------|------|--------|
| Context pack | `_ctx/context_pack.json` | 5.8MB (663 chunks) |
| Aliases | `_ctx/aliases.yaml` | 14KB |
| Anchors | `_ctx/anchors.yaml` | Config linter |
| Config | `_ctx/trifecta_config.json` | Segment config |

### F.4 Progressive Disclosure

| Modo | Descripción |
|------|-------------|
| `raw` | Texto completo con budget check |
| `excerpt` | Primeras 25 líneas + truncation |
| `skeleton` | Headings + code markers + firmas |

### F.5 Observaciones Clave

- **Graph consume, NO modifica**: Lee `context_pack.json`
- **Links**: Tabla `chunk_links` conectará `symbol_id ↔ chunk_id`
- **Señal navegacional**: Graph NO reemplaza PCC

---

## G. Persistencia Local

### G.1 Tabla de Stores

| Store | Ruta | Schema | Propósito |
|-------|------|--------|-----------|
| **AST Cache** | `.trifecta/cache/ast_cache_{segment}.db` | SQLite LRU | Cache de AST parsing |
| **Telemetry Events** | `_ctx/telemetry/events.jsonl` | JSONL | Eventos estructurados |
| **Telemetry Metrics** | `_ctx/telemetry/last_run.json` | JSON | Agregación |
| **Context Pack** | `_ctx/context_pack.json` | JSON (Pydantic) | Meta-contexto curado |
| **Aliases** | `_ctx/aliases.yaml` | YAML | Sinónimos |

### G.2 Schema SQLite AST Cache

```sql
CREATE TABLE cache (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    created_at REAL NOT NULL,
    last_access REAL NOT NULL,
    value_bytes INTEGER NOT NULL
);
CREATE INDEX idx_last_access ON cache(last_access);
```

### G.3 Factory Pattern

```python
# src/infrastructure/factories.py
def get_ast_cache(persist=False, segment_id=".", telemetry=None) -> AstCache:
    if persist:
        return FileLockedAstCache(SQLiteCache(db_path))
    return InMemoryLRUCache()
```

### G.4 Variables de Entorno

| Variable | Efecto |
|----------|--------|
| `TRIFECTA_AST_PERSIST=1` | Habilita cache SQLite persistente |
| `TRIFECTA_TELEMETRY_LEVEL` | off/lite/full |
| `TRIFECTA_PII=allow` | Desactiva saneamiento de rutas |

---

## H. Gaps Reales para Trifecta Graph

### H.1 Faltantes Concretos

| Gap | Descripción | Cambio Requerido |
|-----|-------------|-----------------|
| **Namespace `graph`** | No existe CLI namespace `graph` | Crear `cli_graph.py` con `app = typer.Typer()` + `app.add_typer(graph_app, name="graph")` en cli.py |
| **Symbol ID canónico** | ADR-007 define formato `repo:segment:lang:path:symbol:sig_hash` pero no hay implementación | Crear `src/domain/graph_models.py` con `SymbolID` dataclass + función `canonical_symbol_id()` |
| **Relaciones** | No hay tabla/estructura para `calls`, `imports`, `inherits` | Crear tabla `relations` en SQLite con schema: `(id, source_id, target_id, kind, provenance, confidence, observed_at)` |
| **Links con chunks** | No hay `chunk_links` table | Crear tabla `chunk_links` en SQLite: `(symbol_id, chunk_id, link_status, synced_at)` |
| **Frescura event-based** | No hay estados `fresh/stale/corrupt` | Crear enum `GraphFreshness` en `domain/graph_models.py` con transiciones definidas en ADR-007 |
| **Tree-sitter** | Listado en deps pero NO usado | **NO implementar** - usar `SkeletonMapBuilder` existente como base |
| **Relaciones entre símbolos** | AST actual solo extrae declaraciones, no relaciones | **NO duplicar** - consumir LSP daemon para `call_hierarchy` cuando esté ready, o implementar heurística simple basada en imports |

### H.2 Piezas Parciales Reutilizables

| Pieza | Reutilización | Archivo a modificar/crear |
|-------|---------------|---------------------------|
| `SkeletonMapBuilder` | Base para extracción de símbolos | **NO modificar** - consumir via DI en `GraphIndexer` |
| `AstCache` protocol | Reutilizar para graph cache | Crear `GraphCache` protocol similar en `domain/graph_cache.py` |
| `SQLiteCache` | Patrón para graph.db | Crear `GraphSQLiteStore` siguiendo patrón en `infrastructure/factories.py` |
| `LSPDaemonClient` | Enriquecer relaciones con LSP | **NO duplicar** - inyectar en `GraphIndexer` para call hierarchy |
| `ContextService` | Integrar links con chunks | **NO modificar** - consumir en `GraphLinkService` para validar links |
| Factory pattern | `get_graph_cache()` similar a `get_ast_cache()` | Crear `get_graph_cache()` en `infrastructure/factories.py` |

### H.3 Bloqueos Reales

| Bloqueo | Descripción | Solución |
|---------|-------------|----------|
| **Duplicación SegmentRef** | Dos implementaciones con contratos diferentes | **USAR SOLO** `trifecta/domain/segment_ref.py` - deprecar `domain/segment_resolver.py` |
| **IDs inconsistentes** | AST cache usa path sanitizado, LSP daemon usa SHA256[:8] | Crear función `normalize_segment_id()` en `domain/graph_models.py` que unifique ambos |
| **Sin contrato de relaciones** | ADR-007 lo define pero no hay código | Implementar `GraphRelation` dataclass con campos de ADR-007 |

### H.4 Dependencias Reales para Graph

```
src/domain/graph_models.py       # NUEVO: SymbolID, GraphRelation, GraphFreshness
src/domain/graph_cache.py        # NUEVO: GraphCache protocol
src/application/graph_indexer.py # NUEVO: Orquesta indexación
src/application/graph_service.py # NUEVO: Lógica de queries
src/infrastructure/graph_store.py # NUEVO: SQLite store
src/infrastructure/cli_graph.py  # NUEVO: CLI namespace
```

---

## I. No Duplicar (Lista Explícita)

| # | Pieza Existente | Ubicación | Por qué NO duplicar |
|---|-----------------|-----------|---------------------|
| 1 | **AST parsing** | `src/application/ast_parser.py` | Ya extrae símbolos Python |
| 2 | **AST cache** | `src/domain/ast_cache.py` | Protocolo + implementaciones listas |
| 3 | **LSP client** | `src/infrastructure/lsp_client.py` | JSON-RPC 2.0 completo |
| 4 | **LSP daemon** | `src/infrastructure/lsp_daemon.py` | IPC con socket + lock + TTL |
| 5 | **Context pack** | `_ctx/context_pack.json` | SSOT de chunks, leer solo |
| 6 | **Segment resolution** | `src/trifecta/domain/segment_ref.py` | Usar el primario (9 campos) |
| 7 | **Telemetry** | `src/application/telemetry_pr2.py` | Eventos + reserved keys |
| 8 | **Factory pattern** | `src/infrastructure/factories.py` | Seguir patrón existente |
| 9 | **File locking** | `src/infrastructure/file_locked_cache.py` | Wrapper con timeout |
| 10 | **CLI framework** | `src/infrastructure/cli.py` | Usar Typer, mismo patrón |

### Confusiones Potenciales

| Pieza | Confusión | Realidad |
|-------|-----------|----------|
| `tree-sitter` | "Debe usarse para AST" | NO está implementado, stdlib `ast` se usa |
| `LSPManager` | "Gestiona LSP" | NO se usa, es stub WIP |
| `segment_resolver.py` | "SSOT de segment" | Legacy, usar `trifecta/domain/segment_ref.py` |
| `ast snippet` | "Comando disponible" | NOT_IMPLEMENTED |

---

## J. Recomendación de Siguiente Exploración

### Archivo a revisar inmediatamente

**`ADR/ADR-007-graph-code.md`**

### Por qué

1. Define **contratos de identidad canónica** que no tienen implementación
2. Especifica **schema de relaciones** que debe traducirse a SQLite
3. Define **estados de frescura** (absent/fresh/stale_files/etc.)
4. Establece **boundary graph ↔ context pack** (links, reconciliación)
5. Lista **comandos CLI aprobados** para namespace `graph`

### Después de ADR-007, revisar

1. **`src/trifecta/domain/segment_ref.py`** - Para alinear Graph con SSOT primario
2. **`src/domain/lsp_contracts.py`** - Para reusar `LSPResponse` como modelo de fallback
3. **`src/infrastructure/factories.py`** - Para seguir patrón de factory

---

## Criterio de Éxito - Verificación

Después de leer este informe, puedes responder:

| Pregunta | Respuesta |
|----------|-----------|
| ¿Dónde vive el CLI real? | `src/infrastructure/cli.py` (2739 líneas), entrypoint `src.infrastructure.cli:main` |
| ¿Cuál es el SSOT de segment? | `src/trifecta/domain/segment_ref.py` (9 campos), pero existe duplicación legacy en `src/domain/segment_resolver.py` |
| ¿Qué tenemos de AST? | `SkeletonMapBuilder` con stdlib `ast.parse()`, cache SQLite opcional, NO tree-sitter |
| ¿Qué tenemos de LSP? | Daemon production-ready (socket + lock + TTL), cliente JSON-RPC, fallback explícito |
| ¿Cómo funciona PCC hoy? | `BuildContextPackUseCase` → `_ctx/context_pack.json` (663 chunks), `ContextService` para search/get |
| ¿Qué persistencia existe? | SQLite cache (`.trifecta/cache/`), JSONL telemetry (`_ctx/telemetry/`), JSON pack |
| ¿Qué NO duplicar? | AST parser, AST cache, LSP client/daemon, context pack, factory pattern, file locking |

---

**Fin del informe de exploración técnica.**
