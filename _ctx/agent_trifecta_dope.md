---
segment: .
scope: Verification
repo_root: /workspaces/trifecta_dope
last_verified: 2026-01-05
default_profile: impl_patch
python_version: ">=3.12"
package_manager: uv
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

**Core Dependencies:**
- typer[all]>=0.9.0 (CLI Framework)
- pydantic>=2.0 (Data Models/Schema)
- pyyaml>=6.0 (Artifacts parsing)
- tree-sitter>=0.23.0 (AST Parsing)
- tree-sitter-python>=0.23.0 (Python Language Support)

**Dev Dependencies:**
- pytest>=7.0 (Testing Framework)
- pytest-cov (Coverage)
- ruff (Linting/Formatting)
- mypy (Static Types)
- pyright==1.1.407 (Type Checker)
- bandit[toml]>=1.7.0 (Security Scanner)
- safety>=2.0.0 (Dependency Vulnerability Scanner)

**Telemetry Optional Dependencies:**
- jupyter>=1.0.0 (Analysis Notebooks)
- plotly>=5.18.0 (Interactive Charts)
- pandas>=2.0.0 (Data Analysis)
- kaleido>=0.2.0 (Static Image Export)

**LSP Infrastructure:**
- Daemon: UNIX Socket IPC, Single Instance (Lock), 180s TTL
- Fallback: AST-only if daemon warming/failed
- Audit: No PII, No VFS, Sanitized Paths

**Build System:**
- hatchling (Build Backend)
- uv (Package Manager & Environment)

## Workflow
```bash
# SEGMENT="." es válido SOLO si tu cwd es el repo target.
# Si ejecutas trifecta desde otro lugar, usa un path relativo o variable:
cd /workspaces/trifecta_dope/
# Workflow: Install → Search/Get → Test → Commit
make install
make ctx-search Q="instrucción específica" SEGMENT=.
make gate-all
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
   # INSTRUCCIÓN (not keyword):
   trifecta ctx search --segment . --query "Find documentation about how to implement X feature with examples and contracts" --limit 6
   trifecta ctx get --segment . --ids "<id1>,<id2>" --mode excerpt --budget-token-est 900
   ```

5. **Record Result**:
   ```bash
   trifecta session append --segment . --summary "Completed <task>" --files "<touched>" --commands "<executed>"
   ```

### STALE FAIL-CLOSED Protocol

**CRITICAL**: Si `ctx validate` falla o `stale_detected=true`:

1. **STOP** inmediatamente
2. **Execute**:
   ```bash
   trifecta ctx sync --segment .
   trifecta ctx validate --segment .
   ```
3. **Record** en session.md: `"Stale: true -> sync+validate executed"`
4. **Prohibido** continuar hasta PASS

**Prohibiciones**:
- YAML de historial largo
- Rutas absolutas fuera del segmento
- Scripts legacy de ingestion
- "Fallback silencioso"
- Continuar con pack stale

## Setup

**Entorno Python:**
```bash
# Usando uv (recomendado - maneja Python 3.12+ automáticamente)
make install  # O manualmente: uv sync

# Instalar con telemetry extra (para análisis)
uv sync --extra telemetry

# Activar entorno (opcional)
source .venv/bin/activate
```

**Ejecutar CLI:**
```bash
# Opción 1: Con uv run (no requiere activar entorno)
uv run trifecta ctx search --segment . --query "..."

# Opción 2: Activar entorno y ejecutar directamente
source .venv/bin/activate
trifecta ctx search --segment . --query "..."

# Opción 3: Usar Makefile (recomendado)
make ctx-search Q="búsqueda específica" SEGMENT=.
```

**Variables de Entorno (.env):**
```bash
# Requerido para telemetría
TRIFECTA_TELEMETRY_LEVEL=lite
LSP_DAEMON_TTL_SEC=180  # Default
```

## Gates (Comandos de Verificación)

| Gate | Comando | Propósito |
|------|---------|-----------|
| **Install** | `make install` | Instalar todas las dependencias |
| **Unit** | `make test-unit` | Lógica interna (tests/unit/) |
| **Integration** | `make test-integration` | Flujos CLI/UseCases (tests/integration/) |
| **Acceptance** | `make test-acceptance` | Contratos end-to-end (fast, sin @slow) |
| **Acceptance Slow** | `make test-acceptance-slow` | Tests lentos incluidos |
| **Roadmap** | `make test-roadmap` | Features en progreso |
| **Full Gate** | `make gate-all` | Unit + Integration + Acceptance (Fast) |
| **Audit** | `make audit` | Gate completo + validación de skips |
| **Lint** | `uv run ruff check .` | Calidad de código |
| **Type** | `uv run mypy src/` | Integridad de tipos |
| **Context** | `make ctx-sync` | Sincronizar context pack |

## Active Features (Verified 2026-01-04)

| Feature | Status | Verified | Commands |
|---------|--------|----------|----------|
| **AST Symbols M1** | ✅ PRODUCTION READY | 2026-01-03 | `trifecta ast symbols "sym://..."` |
| **Telemetry System** | ✅ COMPLETE | 2025-12-31 | `trifecta telemetry report/chart/export` |
| **LSP Daemon** | ✅ RELAXED READY | 2026-01-02 | Auto-invoked, 180s TTL, UNIX socket |
| **Error Cards** | ✅ STABLE | 2026-01-02 | `SEGMENT_NOT_INITIALIZED` error type |
| **Deprecation Tracking** | ✅ STABLE | 2026-01-02 | `TRIFECTA_DEPRECATED` env var |
| **Pre-commit Gates** | ✅ STABLE | 2026-01-03 | Zero side-effects guaranteed |
| **ctx plan** | ✅ STABLE | NEW v2.0 | `trifecta ctx plan --segment . --task "..."` |
| **ctx eval-plan** | ✅ STABLE | NEW v2.0 | Evaluate plans against datasets |
| **Obsidian Integration** | ⚠️ EXPERIMENTAL | NONE | Not production-ready, not recommended |

## Troubleshooting

| Problema | Solución |
|----------|----------|
| `ImportError` | `make install` desde el root |
| Python < 3.12 | `uv` maneja automáticamente versión correcta |
| `.env` faltante | Copiar desde `.env.example` y configurar |
| Pack Stale | `make ctx-sync` o `uv run trifecta ctx sync --segment .` |
| Tests Fallan | Revisar logs en `_ctx/telemetry/` |
| CLI no funciona | `uv run trifecta --help` (no requiere activar entorno) |
| Telemetry tools | `uv sync --extra telemetry` para jupyter/plotly |

## Integration Points

**Upstream Dependencies:**
- `pydantic` - Base de modelos de dominio
- `typer` - Motor del CLI
- `pyyaml` - Serialización de estados/config

**Downstream Consumers:**
- Agentes de código que necesiten contexto estructurado
- Autopilot pipelines



## LLM Roles

| Rol | Modelo | Uso |
|-----|--------|-----|
| **Worker** | `deepseek-reasoner` | Tareas generales y razonamiento |
| **Senior** | `claude-sonnet-4-5` | Diseño complejo y refactor |
| **Fallback** | `gemini-3.0-flash-preview` | Recuperación y validación rápida |
