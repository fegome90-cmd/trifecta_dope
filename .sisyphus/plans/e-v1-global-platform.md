# Plan E-V1: Trifecta Global Platform

**Fecha**: 2026-03-06
**Estado**: En progreso (WO-0042 completado)
**Nomenclatura**: E-V1-WO# (para evitar colisiones con WO-004X existentes)

---

## Objetivo

Convertir Trifecta en plataforma local usable desde cualquier parte del Mac.

**Principio clave**: 0041 define → 0042 expone → 0043 opera

---

## Arquitectura: Decisiones Congeladas

### ADR: Native-first Runtime Layout

```
~/.config/trifecta/        # Global config
~/.local/share/trifecta/   # Global state (registry, repos metadata)
~/.cache/trifecta/         # Cache
<global-store>/repos/<repo_id>/
  repo.json           # metadata
  ast.db              # AST cache
  anchors.db          # anchors/symbols
  search.db           # índice búsqueda
  runtime.db          # runtime metadata
  daemon/
    socket
    pid
    log
  locks/
  telemetry/
```

### repo_id Contract

```
repo_id = hash(canonical_repo_path)
- Identifica una instancia local canónica del repo
- Estable mientras la ruta canónica no cambie
- No incluye worktree; worktree/contexto va en segment_id o runtime_key
```

---

## Work Orders

### E-V1-WO1: SSOT + Contratos + Skeleton

**Dependencias**: Ninguna
**Estado**: Pendiente

**Scope (allow)**:
- src/domain/segment_ref.py
- src/domain/repo_ref.py
- src/domain/contracts.py
- src/domain/errors.py
- src/trifecta/platform/registry.py (contract only)
- src/trifecta/platform/runtime_manager.py (skeleton only)
- docs/plans/adr/**
- tests/unit/**

**Scope (deny)**:
- src/infrastructure/cli.py
- src/trifecta/platform/daemon_manager.py (delegado a WO3)
- src/trifecta/platform/repo_store.py (delegado a WO3)
- src/trifecta/infrastructure/sqlite/** (delegado a WO3)

**Objective**:
1. ADRs (3):
   - ADR: SegmentRef SSOT
   - ADR: Platform Runtime
   - ADR: Native-first Runtime Layout
2. SegmentRef / RepoRef:
   - segment_ref.py
   - repo_ref.py
   - resolve_segment_ref() - SINGLE SOURCE OF TRUTH
3. Contratos base:
   - errors.py (PlatformError, RepoNotFoundError, etc.)
   - contracts.py (repo_id contract, segment_id contract)
4. Wrappers deprecated:
   - Marcadores deprecation en código legacy
   - grep guards
5. Tests anti-drift:
   - Verifican que nadie calcule paths/ids a mano
6. Registry mínima (contract-only):
   - Interfaz definida
   - NO implementación completa (delegar a WO3)
7. Skeleton runtime_manager:
   - Interfaz definida
   - NO implementación completa (delegar a WO3)

**Verify**:
```bash
uv run pytest -q tests/unit/test_segment_ref.py
uv run ruff check src/domain/
grep -rE "(compute_segment_id|normalize_segment_id|sha256\(.*path)" src/ --include="*.py" | grep -v "__pycache__" | wc -l
```

---

### E-V1-WO2: CLI Adelgazado + Repo Commands

**Dependencias**: E-V1-WO1
**Estado**: ✅ COMPLETADO (2026-03-06)

**Entregado**:
- src/application/status_use_case.py
- src/application/doctor_use_case.py
- src/application/repo_use_case.py
- src/infrastructure/cli.py (comandos nuevos)
- tests/integration/cli/**
- CLI: trifecta status --repo, trifecta doctor --repo, trifecta repo register/list/show
- Flag --json con schema estable

**Verify**:
```bash
uv run pytest -q tests/integration/cli/ -k "test_status or test_doctor or test_repo"
uv run ruff check src/application/
```

---

### E-V1-WO3: SQLite + Daemon + Operación Real

**Dependencias**: E-V1-WO1, E-V1-WO2
**Estado**: Pendiente

**Scope (allow)**:
- src/trifecta/platform/daemon_manager.py
- src/trifecta/platform/repo_store.py
- src/trifecta/platform/health.py
- src/trifecta/application/index_use_case.py
- src/trifecta/application/query_use_case.py
- src/trifecta/application/daemon_use_case.py
- src/trifecta/infrastructure/sqlite/**
- tests/integration/runtime/**
- tests/integration/daemon/**

**Scope (deny)**:
- src/infrastructure/lsp_*.py (refactor MASIVO prohibido)
- Se permiten adapters/wrappers mínimos hacia LSP legacy si son estrictamente necesarios

**Objective**:
1. Repo Store Real:
   - repo_store.py con SQLite
   - CRUD de repos registrados
   - Aislamiento por repo_id
2. SQLite per-repo:
   - ast.db, anchors.db, search.db, runtime.db
   - Esquemas versionados
   - Reindex no afecta otros repos
3. Daemon Manager:
   - daemon_manager.py
   - start/stop/status/restart
   - On-demand: levanta si no existe
   - Reutiliza si ya está sano
   - TTL para idle
   - Recovery ante socket muerto
4. Health:
   - health.py
   - Healthcheck real
   - Runtime readiness
5. Index/Query Wiring:
   - index_use_case.py
   - query_use_case.py
   - Wiring a search.db
6. Comandos V1 restantes:
   - trifecta index --repo <path>
   - trifecta query --repo <path> "query"
   - trifecta daemon start|stop|status|restart --repo <path>

**Verify**:
```bash
uv run pytest -q tests/integration/runtime/ -k "test_daemon or test_store"
uv run ruff check src/trifecta/platform/
```

---

## Layout Final src/trifecta/

```
src/trifecta/
├── domain/
│   ├── segment_ref.py      # SSOT - resolución paths/ids
│   ├── repo_ref.py         # Repo reference
│   ├── contracts.py        # Contratos (repo_id, segment_id)
│   └── errors.py           # Errores específicos
│
├── application/
│   ├── status_use_case.py  # WO2
│   ├── doctor_use_case.py  # WO2
│   ├── repo_use_case.py    # WO2
│   ├── index_use_case.py   # WO3
│   ├── query_use_case.py   # WO3
│   └── daemon_use_case.py  # WO3
│
├── platform/
│   ├── registry.py         # WO1 (contract) → WO3 (impl)
│   ├── runtime_manager.py  # WO1 (skeleton) → WO3 (impl)
│   ├── daemon_manager.py   # WO3
│   ├── repo_store.py      # WO3
│   └── health.py           # WO3
│
├── infrastructure/
│   └── sqlite/             # WO3
│
└── interfaces/
    └── cli/                 # WO2 (nueva fachada)
```

---

## Criterios de Aceptación V1

### Arquitectónicos
- [ ] Existe UNA SOLA función oficial para resolver repo/segment/path/runtime
- [ ] El CLI NO crea paths críticos por su cuenta
- [ ] El daemon NO es fuente de verdad (truth = SSOT + store + contracts)
- [ ] El runtime por repo es aislado
- [ ] La salida JSON del CLI tiene contrato estable

### Operacionales
- [ ] El sistema corre SIN Docker
- [ ] El sistema corre SIN servicios externos
- [ ] Un repo puede ser reindexado SIN afectar otro
- [ ] Un daemon muerto puede recuperarse SIN intervención manual compleja

---

## Feedback Incorporado

1. **Paths Unificados**: src/trifecta/interfaces/cli/ como destino final, src/infrastructure/cli.py como wrapper legacy
2. **WO1 Acotado**: Solo SSOT + contratos + skeleton, delegate repo_store/daemon a WO3
3. **Negación WO3**: "refactor MASIVO prohibido" (no "todo LSP")
4. **repo_id Explicitado**: Instancia local canónica, no "repo lógico Git"
5. **RepoContext/SegmentRef**: Objeto de cruce de capas congelado
6. **Verify Commands**: Endurecidos y focalizados por capa

---

## Ejecución

```bash
# Orden: WO1 → WO2 → WO3
# 1. E-V1-WO1
make install
make wo-preflight WO=E-V1-WO1
uv run python scripts/ctx_wo_take.py E-V1-WO1

# 2. E-V1-WO2 (ya completado)
# 3. E-V1-WO3
make install
make wo-preflight WO=E-V1-WO3
uv run python scripts/ctx_wo_take.py E-V1-WO3
```
