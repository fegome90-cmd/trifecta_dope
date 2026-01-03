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

**Entorno Python (Recomendado):**
```bash
# Usando uv (rápido y determinístico)
uv sync
source .venv/bin/activate
```

**Variables de Entorno (.env):**
```bash
# Requerido para telemetría y LiteLLM (si aplica)
TRIFECTA_TELEMETRY_LEVEL=lite
LSP_DAEMON_TTL_SEC=180 # Default
```

## Gates (Comandos de Verificación)

| Gate | Comando | Propósito |
|------|---------|-----------|
| **Unit** | `uv run pytest tests/unit/ -v` | Lógica interna |
| **Integración** | `uv run pytest tests/test_use_cases.py -v` | Flujos CLI/UseCases |
| **Daemon Tripwires** | `uv run pytest tests/integration/test_lsp_daemon.py` | Validar Lifecycle/TTL |
| **Lint** | `uv run ruff check .` | Calidad de código |
| **Type** | `uv run mypy src/` | Integridad de tipos |
| **Context** | `uv run trifecta ctx validate --segment .` | Integridad del pack |

## Troubleshooting

| Problema | Solución |
|----------|----------|
| `ImportError` | `uv pip install -e .` desde el root |
| `.env` faltante | Copiar desde `.env.example` y configurar |
| Pack Stale | `uv run trifecta ctx sync --segment .` |
| Fallos en Tests | Revisar logs en `_ctx/telemetry/` |

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
