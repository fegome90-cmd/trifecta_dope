# Plan Corregido V2: Trifecta V1 Global Platform - Work Orders

## TL;DR

> **Objetivo**: Convertir Trifecta en plataforma local usable desde cualquier parte del Mac.
>
> **Entregables**: 1 Epic + 4 Work Orders
>
> **Principio clave**: WO-0041 define → WO-0042 expone → WO-0043 opera

---

## Feedback Incorporado (5 puntos finales)

### 1. Repo_id - Significado Correcto
**Corrección**:
```
repo_id = hash(canonical_repo_path)
- Identifica una instancia local canónica del repo
- Estable mientras la ruta canónica no cambie
- No incluye worktree; worktree/contexto va en segment_id o runtime_key
```
**No es "repo lógico Git"** - es instancia local.

---

### 2. Verify --json - Entrypoint Controlado
**Antes**: `uv run trifecta status --repo . --json | python -m json.tool`
**Ahora**: Usar entrypoint de test controlado:
```bash
# En tests/integration/cli/ debe existir fixture de repo
uv run pytest -q tests/integration/cli/test_status_json.py -k "test_status_json_output"
```
O equivalente que no asuma instalación global.

---

### 3. Verify Recovery - Kill Dirigido
**Antes**: `pkill -f trifecta-daemon`
**Ahora**:
```bash
# 1. Obtener PID desde runtime del repo
RUNTIME_DIR="~/.local/share/trifecta/repos/<repo_id>/runtime"
PID=$(cat "$RUNTIME_DIR/daemon/pid")

# 2. Matar ese PID puntual
kill $PID 2>/dev/null || true

# 3. Verificar que status detecta muerto y reporta correctamente
uv run trifecta daemon status --repo <path>
# Debe decir: "daemon not running" o "recovering"
```

---

### 4. Grep Guards - Más Semánticos
**Antes**: `grep -r "repo_id ="`
**Ahora**: Buscar patrones de cálculo manual:
```bash
# Patterns que indican cálculo manual de segment_id / repo_id:
# - compute_segment_id
# - normalize_segment_id  
# - sha256.*path
# - hashlib.*repo
# - os.path.*sin usar resolve_segment_ref

# Test de contrato:
uv run pytest -q tests/contracts/test_segment_ref_contract.py -k "test_all_use_cases_call_resolver"
```

---

### 5. RepoContext/SegmentRef - Objeto de Cruce
**Agregado en WO-0041**:
```python
# El resolve_segment_ref() retorna un objeto estable:

@dataclass(frozen=True)
class SegmentRef:
    repo_root: Path
    repo_id: str                    # hash(canonical_path)
    segment_root: Path
    segment_id: str                 # runtime key si aplica
    runtime_dir: Path
    registry_key: str
    telemetry_dir: Path
    config_dir: Path
    cache_dir: Path
```

**Este contrato es el que consumen registry, use cases y runtime.**
---

## Arquitectura V1: Decisiones Congeladas

### ADR: Native-first Runtime Layout
```
~/.config/trifecta/        # Global config
~/.local/share/trifecta/   # Global state (registry, repos metadata)
~/.cache/trifecta/        # Cache

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
  - Identifica instancia local canónica del repo
  - Estable mientras la ruta no cambie
  - No incluye worktree
```

### segment_id / runtime_key
```
segment_id o runtime_key = identifica worktree/contexto específico
  - Necesario si el mismo repo tiene múltiples worktrees
  - Derivado de git worktree o path específico
```

---

## TODOs

### Tarea 1: Epic E-V1

**What to do**:
- Agregar `E-V1` a `_ctx/backlog/backlog.yaml`

**Acceptance**:
- [ ] Existe en backlog.yaml
- [ ] 4 WOs asociados (0040, 0041, 0042, 0043)

---

### Tarea 2: E-V1-WO0 - Roadmap Master (Tracking-Only)

**What to do**:
- Crear `_ctx/jobs/pending/E-V1-WO0.yaml`

**Scope**:
- allow: docs/plans/*, backlog.yaml, WO-*.yaml
- deny: src/**

**Objective**:
```
WO de tracking no ejecutable.
No crea runtime, no modifica dominio, no introduce código productivo.
Sirve como entry-point documental del roadmap V1.
```

**Verify**:
```yaml
commands:
  - uv run python scripts/ctx_backlog_validate.py --strict
```

---

### Tarea 3: E-V1-WO1 - SSOT + Contratos + Skeleton

**What to do**:
- Crear `_ctx/jobs/pending/E-V1-WO1.yaml`

**Scope (allow)**:
```
src/domain/**
src/platform/registry.py        # contract-only
src/platform/runtime_manager.py # skeleton-only
docs/plans/**
tests/unit/**
tests/contracts/**
```

**Scope (deny)**:
```
src/infrastructure/cli.py
src/platform/daemon_manager.py
src/platform/repo_store.py
src/infrastructure/sqlite/**
```

**Objective**:
```
1. ADRs (3):
   - ADR: SegmentRef SSOT
   - ADR: Platform Runtime
   - ADR: Native-first Runtime Layout

2. SegmentRef / RepoRef:
   - segment_ref.py
   - repo_ref.py
   - resolve_segment_ref() - SINGLE SOURCE OF TRUTH
   - Retorna objeto SegmentRef (ver below)

3. SegmentRef Contract (OBJETO DE CRUCE):
@dataclass(frozen=True)
class SegmentRef:
    repo_root: Path
    repo_id: str                    # hash(canonical_path)
    segment_root: Path
    segment_id: str                 # runtime key
    runtime_dir: Path
    registry_key: str
    telemetry_dir: Path
    config_dir: Path
    cache_dir: Path

4. Contratos base:
   - errors.py (PlatformError, RepoNotFoundError, SegmentNotFoundError)
   - contracts.py (repo_id contract, segment_id contract)

5. Wrappers deprecated:
   - Funciones legacy que delegan a resolve_segment_ref()
   - Warnings deprecation

6. Tests contracts:
   - tests/contracts/test_segment_ref_contract.py
   - Verifica que todos los use cases usen el resolver oficial

7. Registry mínima (contract-only):
   - Interfaz/abstracta definida
   - NO implementación

8. Skeleton runtime_manager:
   - Interfaz definida
   - NO implementación
```

**Verify (focalizado)**:
```yaml
commands:
  - uv run pytest -q tests/unit/test_segment_ref.py
  - uv run pytest -q tests/contracts/test_segment_ref_contract.py
  - uv run ruff check src/domain/
  # Grep guards más semánticos:
  - rg "compute_segment_id|normalize_segment_id|sha256.*path" src/ --type py | wc -l  # debe ser 0
```

**Acceptance Criteria**:
- [ ] 3 ADRs creados en docs/plans/
- [ ] resolve_segment_ref() retorna SegmentRef object
- [ ] SegmentRef tiene todos los campos definidos
- [ ] Tests contracts verifican uso del resolver
- [ ] repo_id contract documentado
- [ ] Wrappers deprecated con warnings

---

### Tarea 4: E-V1-WO2 - CLI Adelgazado + Repo Commands

**What to do**:
- Crear `_ctx/jobs/pending/E-V1-WO2.yaml`
- **Dependencia**: E-V1-WO1

**Scope (allow)**:
```
src/application/status_use_case.py
src/application/doctor_use_case.py
src/application/repo_use_case.py
src/interfaces/cli/**
src/infrastructure/cli.py   # wrapper/compat
tests/integration/cli/**
```

**Scope (deny)**:
```
src/platform/daemon_manager.py
src/platform/repo_store.py
src/infrastructure/sqlite/**
```

**Objective**:
```
1. Fachada CLI delgada:
   - parse args → validate → use case → render
   - NO construir repo_id a mano
   - NO levantar daemons
   - NO abrir DBs arbitrariamente

2. Comandos V1:
   - trifecta status --repo <path>
   - trifecta doctor --repo <path>
   - trifecta repo register <path>
   - trifecta repo list
   - trifecta repo show <repo_id>

3. Salida estable:
   - --json flag
   - exit codes claros (0=ok, 1=error, 2=validation)
   - JSON schema estable

4. Wrapper legacy:
   - src/infrastructure/cli.py delega a src/interfaces/cli/
```

**Verify (focalizado)**:
```yaml
commands:
  - uv run pytest -q tests/integration/cli/ -k "test_status or test_doctor or test_repo"
  - uv run ruff check src/interfaces/cli/
  # Verificar --json con entrypoint de test controlado:
  - uv run pytest -q tests/integration/cli/test_status_json.py -k "test_status_json_valid"
```

**Acceptance Criteria**:
- [ ] CLI usa resolve_segment_ref() para paths
- [ ] status, doctor, repo commands funcionan
- [ ] --json produce JSON válido
- [ ] Exit codes estables

---

### Tarea 5: E-V1-WO3 - SQLite + Daemon + Operación Real

**What to do**:
- Crear `_ctx/jobs/pending/E-V1-WO3.yaml`
- **Dependencias**: E-V1-WO1, E-V1-WO2

**Scope (allow)**:
```
src/platform/daemon_manager.py
src/platform/repo_store.py
src/platform/health.py
src/application/index_use_case.py
src/application/query_use_case.py
src/application/daemon_use_case.py
src/infrastructure/sqlite/**
src/interfaces/cli/**
tests/integration/runtime/**
tests/integration/daemon/**
```

**Scope (deny)**:
```
# Se permiten adapters/wrappers mínimos hacia LSP legacy si son estrictamente necesarios.
# Se prohíbe refactor MASIVO del subsistema LSP.
```

**Objective**:
```
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
```

**Verify (focalizado)**:
```yaml
commands:
  - uv run pytest -q tests/integration/runtime/ -k "test_daemon or test_store"
  - uv run ruff check src/platform/
  # Verify recovery con kill dirigido:
  - uv run pytest -q tests/integration/daemon/test_recovery.py -k "test_daemon_recovers_on_death"
```

**Recovery Test Detallado**:
```python
# 1. Start daemon
runner = CliRunner()
result = runner.invoke(daemon_start, ["--repo", fixture_repo])

# 2. Get PID from runtime
pid_file = Path(f"{runtime_dir}/daemon/pid")
original_pid = pid_file.read_text().strip()

# 3. Kill daemon process directly (NOT pkill -f)
os.kill(int(original_pid), signal.SIGTERM)

# 4. Verify status detects death
result = runner.invoke(daemon_status, ["--repo", fixture_repo])
assert "not running" in result.output or "recovering" in result.output

# 5. Verify daemon can be restarted
result = runner.invoke(daemon_start, ["--repo", fixture_repo])
assert result.exit_code == 0
```

**Acceptance Criteria**:
- [ ] Registry mínimo operativo
- [ ] Daemon se levanta/reutiliza por repo
- [ ] Healthcheck real funciona
- [ ] SQLite aisla por repo
- [ ] index/query funcionan
- [ ] Recovery ante muerte de proceso funciona

---

## Layout Final src/

```
src/
├── domain/
│   ├── segment_ref.py      # ✅ SSOT + SegmentRef object
│   ├── repo_ref.py         # ✅ Repo reference
│   ├── contracts.py        # ✅ Contratos
│   └── errors.py           # ✅ Errores específicos
│
├── application/
│   ├── status_use_case.py  # ✅ 0042
│   ├── doctor_use_case.py  # ✅ 0042
│   ├── repo_use_case.py    # ✅ 0042
│   ├── index_use_case.py   # ✅ 0043
│   ├── query_use_case.py   # ✅ 0043
│   └── daemon_use_case.py  # ✅ 0043
│
├── platform/
│   ├── registry.py         # ✅ 0041 (contract) → 0043 (impl)
│   ├── runtime_manager.py  # ✅ 0041 (skeleton) → 0043 (impl)
│   ├── daemon_manager.py   # ✅ 0043
│   ├── repo_store.py       # ✅ 0043
│   └── health.py           # ✅ 0043
│
├── infrastructure/
│   └── sqlite/             # ✅ 0043
│
└── interfaces/
    └── cli/                # ✅ 0042
```

---

## Criterios de Aceptación V1

### Arquitectónicos
- [ ] Una sola función oficial: resolve_segment_ref()
- [ ] Retorna SegmentRef object con todos los campos
- [ ] CLI NO calcula paths/ids manualmente
- [ ] Daemon NO es fuente de verdad
- [ ] Runtime aisla por repo
- [ ] JSON output tiene contrato estable

### Operacionales
- [ ] Sin Docker
- [ ] Sin servicios externos
- [ ] Reindex de un repo no afecta otros
- [ ] Recovery de daemon sin intervención manual compleja

---

## Ejecución

```bash
# Orden: 0041 → 0042 → 0043 (0040 es tracking-only)

# 1. Crear Epic E-V1
# (editar backlog.yaml)

# 2. Crear WOs
# (copiar YAMLs)

# 3. Validar
uv run python scripts/ctx_backlog_validate.py --strict

# 4. Ejecutar
uv run python scripts/ctx_wo_take.py E-V1-WO1
```

---

## Success Criteria

- [ ] 1 Epic + 4 WOs creados y validados
- [ ] E-V1-WO1: SSOT + SegmentRef object + contracts
- [ ] E-V1-WO2: CLI delgada + --json estable
- [ ] E-V1-WO3: SQLite + daemon + recovery
- [ ] Criterios arquitectónicos cumplidos
- [ ] Criterios operacionales cumplidos
