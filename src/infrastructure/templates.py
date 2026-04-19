"""Template Renderer for Trifecta files."""

from src.domain.models import TrifectaConfig


class TemplateRenderer:
    """Renders Trifecta templates."""

    def render_skill(self, config: TrifectaConfig) -> str:
        return f"""---
name: {config.segment}
description: Use when working on {config.scope}
---

# {config.segment.replace("-", " ").title()}

## Overview
{config.scope}

## When to Use
Working on `{config.repo_root}/{config.segment}/`

## Core Pattern

### Session Evidence Persistence (5 Steps)

1) **Persist intention** (CLI proactive):
```bash
trifecta session append --segment . --summary "<action>" --files "<csv>" --commands "<csv>"
```

2) **Sync context**:
```bash
trifecta ctx sync --segment .
```

3) **Read** session.md (confirm objective logged)

4) **Execute** context cycle:
```bash
trifecta ctx search --segment . --query "<topic>" --limit 6
trifecta ctx get --segment . --ids "<id1>,<id2>" --mode excerpt --budget-token-est 900
```

5) **Log result**:
```bash
trifecta session append --segment . --summary "Completed <task>" --files "<touched>" --commands "<executed>"
```

### Mandatory Validation Protocol (Law V)

**STALE FAIL-CLOSED**: If `ctx validate` fails or `stale_detected=true`:
- **STOP** immediately. Do NOT guess.
- Run: `trifecta ctx sync --segment .` + `trifecta ctx validate --segment .`
- Continue ONLY if state is **VALID**.
- **Evidence**: All mutations MUST be followed by a verification command.

## Common Mistakes
- Skipping session logging (Law I violation)
- Writing before reading (Law II violation)
- Continuing with stale pack (Law VI violation)
- Model-specific bias in naming (Law VII violation)

## Resources (On-Demand)
- `@_ctx/prime_{config.segment}.md` - Reading list
- `@_ctx/agent_{config.segment}.md` - Tech stack & gates
- `@_ctx/session_{config.segment}.md` - Session log

---
**Profile**: `{config.default_profile}` | **Updated**: {config.last_verified}
"""

    def render_prime(self, config: TrifectaConfig, docs: list[str]) -> str:
        # Format docs with priority indicators
        formatted_docs = ""
        if docs:
            for i, doc in enumerate(docs):
                formatted_docs += f"{i + 1}. `{doc}`\n"
        else:
            formatted_docs = "<!-- Agregar documentos obligatorios -->"

        return f"""---
segment: {config.segment}
profile: load_only
---

# Prime {config.segment.replace("-", " ").title()} - Lista de Lectura

> **SEGMENT_ROOT**: `.` (all paths relative to segment root)
>
> **Orden de lectura**: Fundamentos -> Implementacion -> Referencias

## [HIGH] Prioridad ALTA - Fundamentos

**Leer primero para entender el contexto del segmento.**

{formatted_docs}

## [MED] Prioridad MEDIA - Implementacion

<!-- Documentacion de implementacion especifica -->

## [LOW] Prioridad BAJA - Referencias

<!-- Documentacion de referencia, archivada -->

## [MAP] Mapa Mental

```mermaid
mindmap
  root({config.segment})
    Fundamentos
    Arquitectura
    Interfaces
```

## [DICT] Glosario

| Termino | Definicion |
|---------|------------|
| <!-- Terminos clave --> | <!-- Definiciones --> |

## [NOTE] Notas

- **Fecha ultima actualizacion**: {config.last_verified}
- **Mantenedor**: <!-- Agregar si aplica -->
- **Ver tambien**: [skill.md](skill.md) | [AGENTS.md](AGENTS.md)
"""

    def render_agent(self, config: TrifectaConfig) -> str:
        return f"""---
segment: {config.segment}
scope: {config.scope}
repo_root: {config.repo_root}
last_verified: {config.last_verified}
default_profile: {config.default_profile}
---

# Agent Context - {config.segment.replace("-", " ").title()}

## Source of Truth
| Seccion | Fuente |
|---------|--------|
| LLM Roles | [skill.md](../skill.md) |
| Governance | [AGENTS.md](../AGENTS.md) |

## Tech Stack
**Lenguajes:**
- <!-- Ej: Python 3.12+, TypeScript 5.x -->

**Frameworks:**
- <!-- Ej: FastAPI, Pydantic v2 -->

**Herramientas:**
- <!-- Ej: pytest, ruff, uv -->

## Gates (Comandos de Verificacion)

**Unit Tests:**
```bash
pytest tests/unit/ -v
```

**Linting:**
```bash
ruff check .
```

**Type Checking:**
```bash
mypy src/
```

## Resilience Boundaries
- **Message Cap**: 5,000 messages (Circular Buffer)
- **Disk Safety**: 60s TTL for ephemeral handoffs in `.ai/traces/`

## Deep Intelligence Persistence
- **Symbol Graph**: `_ctx/graph.db` (SQLite)
- **AST Cache**: `.trifecta/cache/ast_cache_*.db` (SQLite)
- **LSP Socket**: `/tmp/trifecta_lsp_<id>.sock` (Unix Domain Socket)
"""

    def render_session(self, config: TrifectaConfig) -> str:
        return f"""# session.md - Trifecta Context Runbook

segment: {config.segment}

## Purpose
This file is a **runbook** for using Trifecta Context tools following the **Agentic Constitution v1.1**.

## Quick Commands (CLI)

### 🛰️ Basic Context (PCC)
```bash
# [Law II] Reading before writing
make sync
make search Q="<topic>"
trifecta ctx get --segment "." --ids "<id>" --mode excerpt
```

### 🧠 Intelligent Discovery (AST & LSP)
```bash
# Discover symbols in Python (Class, Def, Import)
# URI format: sym://python/mod/<path.to.module>
trifecta ast symbols "sym://python/mod/src.infrastructure.cli"

# LSP Hover (Definition + Type info) - Requires Warmup
trifecta ast hover "src/infrastructure/cli.py" --line 1672 --char 5
```

### 🕸️ Relationship Mapping (Graph)
```bash
# Find who calls a specific function
trifecta graph callers --symbol "create"

# Find what functions a specific function calls
trifecta graph callees --symbol "TemplateRenderer.render_skill"
```

### 🩺 System Maintenance
```bash
# [Law V] Verification
trifecta ctx validate --segment "."

# Global Status & Health
make status
make doctor
```

## Rules (must follow)
* Max **1 ctx.search + 1 ctx.get** per user turn.
* Cite evidence using **[chunk_id]** (Law IV & XI).
* **FAIL-CLOSED**: If validate fails, STOP.

## Session Log (append-only)

### Entry Template (Law I & XI)
```md
## YYYY-MM-DD HH:MM - ctx cycle
- Segment: .
- Objective: <Law I: Intencion explicita>
- Plan: ctx sync -> ctx search -> ctx get
- Evidence: <Law IV: Evidencia obligatoria>
- Next: <1 concrete step>
```
"""

    def render_readme(self, config: TrifectaConfig) -> str:
        return f"""# {config.segment.replace("-", " ").title()} - Trifecta Documentation

> **Trifecta F1 Engine**: Repositorio blindado bajo la **Constitucion de Codigo Agentico v1.1**.

## [FILE] Estructura Neutral (Ley VII)

```
{config.segment}/
|-- AGENTS.md                    # Constitucion y Gobernanza (Vinculante)
|-- skill.md                     # Reglas y contratos (Protocolo Fail-Closed)
|-- .ai/                         # [Neutral] Infraestructura agentica
|   |-- commands/                # Comandos personalizados
|   |-- hooks/                   # Automatizacion event-driven
|   |-- plans/                   # Planes de ejecucion
|   |__ traces/                  # Evidencia y logs de sesion
|-- scripts/
|   |__ trifecta_manager.sh      # Authoritative Daemon & Health Manager
|-- configs/
|   |-- anchors.yaml             # Semantic anchors for agents
|   |__ aliases.yaml             # Common phrase mappings
|-- Makefile                     # Unified Command Interface (F1 Style)
|-- biome.json                   # Quality: Formatter & Linter config
|-- pyrefly.toml                 # Quality: Type-checking config
|-- llms.txt                     # LLM Reference guide
|__ _ctx/                        # Context resources (PCC)
```

## [CLEAN] Repository Hygiene (Mandatory)

Para mantener el motor de Trifecta calibrado, el repositorio MUST estar limpio.

```bash
# Purga de worktrees redundantes
make clean
```

## [GO] Flujo de Onboarding

1. **Leer `AGENTS.md`** - Entender las 13 Leyes.
2. **Leer `skill.md`** - Activar el protocolo de validacion.
3. **Deep Context Activation** - Run `make warmup`.
4. **Leer `_ctx/prime_{config.segment}.md`** - Cargar lista de lectura.

> [!IMPORTANT]
> **Toda mutacion sin plan previo es una violacion de la Ley I.**
"""

    def render_agents_md(self, config: TrifectaConfig) -> str:
        return f"""# {config.segment.replace("-", " ").title()} - AGENTS.md

> **Generated**: {config.last_verified} | **Governance**: Constitucion AI v1.1

## 🏛️ Gobernanza Agéntica

Este repositorio opera bajo la **Constitucion de Codigo Agentico v1.1**. 
Source of Truth: `https://github.com/fegome90-cmd/constitucion-ai`

### Las 13 Leyes (Destiladas)

1. **Cambio Legitimo**: Intencion -> Plan -> Validacion -> Evidencia.
2. **Lectura Previa**: Prohibido escribir sin haber leido el contexto relevante.
3. **Arquitectura Base**: Respetar el Scope y la jerarquia del sistema.
4. **Control de Versiones**: Aislamiento total en ramas y worktrees.
5. **Verificabilidad**: Ningun cambio es real sin evidencia de ejecucion.
6. **Fuente de Verdad**: Sincronizacion obligatoria ante cualquier duda.
7. **Primacia del Sistema**: Neutralidad absoluta. Usar directorio `.ai/`.
8. **Seguridad**: Proteccion de secretos y limites de permisos.
9. **Persistencia**: Estado trazable y recuperable.
10. **Interfaces**: Respetar contratos y compatibilidad.
11. **Observabilidad**: Registro mandatorio de acciones en `_ctx/session`.
12. **Roles**: Actuar dentro de las capacidades de la Skill.
13. **Primacia Conceptual**: Priorizar el entendimiento semantico.

## 🛠️ Procedimiento de Checkpoint

Al finalizar cada tarea, el agente MUST:
1. Generar evidencia de validacion (logs/tests).
2. Actualizar el log de sesion en `_ctx/session_{config.segment}.md`.
3. Guardar un handoff en `.ai/traces/` si el trabajo continua.

---
**Neutralidad**: Este repositorio no tiene preferencia por modelos especificos.
"""

    def render_ai_settings(self) -> str:
        return """{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": ".ai/hooks/session-end-hook.sh"
          }
        ]
      }
    ]
  }
}
"""

    def render_daemon_manager_sh(self, config: TrifectaConfig, repo_id: str) -> str:
        script = r'''#!/bin/bash
# scripts/trifecta_manager.sh - Authoritative lifecycle manager for Trifecta Daemon
# Standard F1 Engine Orchestration v2 (Stage 3 Deep Intel)

set -euo pipefail

REPO_ID="REPLACE_REPO_ID"
PID_FILE="$HOME/.local/share/trifecta/repos/$REPO_ID/runtime/daemon/pid"
LOCK_FILE="$HOME/.local/share/trifecta/repos/$REPO_ID/runtime/daemon/lock"
STATUS_JSON="_ctx/telemetry/daemon.status"

# Multi-tier resilient binary detection
if command -v trifecta >/dev/null 2>&1 && trifecta graph --help >/dev/null 2>&1; then
    TRIFECTA_BIN="trifecta"
elif [[ -f "./.venv/bin/trifecta" ]]; then
    TRIFECTA_BIN="./.venv/bin/trifecta"
elif command -v uv >/dev/null 2>&1 && [[ -f "pyproject.toml" ]]; then
    TRIFECTA_BIN="uv run trifecta"
else
    # Total fallback: notify agent
    echo "[trifecta-manager] CRITICAL: Valid 'trifecta' binary with Graph support not found."
    echo "Hint: Install latest trifecta or initialize a uv environment."
    exit 1
fi

# Ensure telemetry dir exists
mkdir -p _ctx/telemetry

_update_status_json() {
    local pid="${1:-0}"
    local status="${2:-unknown}"
    local now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    # Sanitize PID
    pid="${pid//[^0-9]/}"
    pid="${pid:-0}"

    cat <<EOF > "$STATUS_JSON"
{
  "pid": $pid,
  "status": "$status",
  "last_check": "$now",
  "repo_id": "$REPO_ID"
}
EOF
}

_is_process_running() {
    local pid="$1"
    if [[ -z "$pid" ]] || [[ "$pid" == "0" ]]; then return 1; fi
    # Check if process exists AND is a trifecta daemon
    if ps -p "$pid" > /dev/null 2>&1; then
        if ps -p "$pid" -o args= 2>/dev/null | grep -q "daemon"; then
            return 0
        fi
    fi
    return 1
}

_prune_zombies() {
    local current_pid=$(cat "$PID_FILE" 2>/dev/null || echo "0")
    if ! _is_process_running "$current_pid"; then
        echo "[trifecta-manager] Pruning stale state (PID $current_pid not found)..."
        rm -f "$PID_FILE" "$LOCK_FILE"
    fi
}

_check_lsp_binary() {
    if command -v pyright >/dev/null 2>&1 || command -v pylsp >/dev/null 2>&1; then
        return 0
    fi
    return 1
}

status() {
    local pid=$(cat "$PID_FILE" 2>/dev/null || echo "0")
    if _is_process_running "$pid"; then
        echo "Daemon: running (PID: $pid)"
        _update_status_json "$pid" "running"
        return 0
    else
        echo "Daemon: stopped"
        _update_status_json 0 "stopped"
        return 1
    fi
}

start() {
    _prune_zombies
    local pid=$(cat "$PID_FILE" 2>/dev/null || echo "0")
    if _is_process_running "$pid"; then
        echo "Daemon already running (PID: $pid)"
        return 0
    fi

    if ! _check_lsp_binary; then
        echo "[trifecta-manager] WARNING: No LSP binary (pyright/pylsp) found. Daemon will run in AST-only mode."
    fi

    echo "[trifecta-manager] Starting daemon..."
    if $TRIFECTA_BIN daemon start --repo . > /dev/null 2>&1; then
        sleep 1
        local new_pid=$(cat "$PID_FILE" 2>/dev/null || echo "0")
        if _is_process_running "$new_pid"; then
            echo "Daemon started successfully (PID: $new_pid)"
            _update_status_json "$new_pid" "running"
            return 0
        fi
    fi

    echo "ERROR: Failed to start daemon"
    _update_status_json 0 "error"
    return 1
}

stop() {
    local pid=$(cat "$PID_FILE" 2>/dev/null || echo "0")
    if _is_process_running "$pid"; then
        echo "[trifecta-manager] Stopping daemon (PID: $pid)..."
        kill "$pid" 2>/dev/null || true
        sleep 1
    fi
    # Hard cleanup
    rm -f "$PID_FILE" "$LOCK_FILE"
    echo "Daemon stopped"
    _update_status_json 0 "stopped"
}

restart() {
    stop
    start
}

health() {
    local pid=$(cat "$PID_FILE" 2>/dev/null || echo "0")
    if ! _is_process_running "$pid"; then
        echo "[trifecta-manager] Unhealthy state detected. Attempting recovery..."
        start
    else
        echo "Daemon is healthy (PID: $pid)"
        _update_status_json "$pid" "healthy"
    fi
}

warmup() {
    echo "[trifecta-manager] Launching Ignition Sequence (Full Stack)..."
    
    echo "[1/3] Building Context Pack (sync)..."
    if $TRIFECTA_BIN ctx sync --segment . ; then
        echo "✅ Context synchronized and chunks generated."
    else
        echo "❌ FAILED: Context sync failed."
        exit 1
    fi

    echo "[2/3] Building Symbol Graph (graph index)..."
    if $TRIFECTA_BIN graph index --segment . ; then
        echo "✅ Graph built successfully."
    else
        echo "❌ FAILED: Graph build failed."
        exit 1
    fi

    echo "[3/3] Starting Daemon (LSP)..."
    start
    
    echo ""
    echo "=== F1 ENGINE SOVEREIGN BIRTH COMPLETE ==="
    echo "Context built, Graph indexed, Daemon alive."
    echo "The repository is now fully operational for AI Agents."
}

case "${1:-status}" in
    start) start ;;
    stop) stop ;;
    restart) restart ;;
    status) status ;;
    health) health ;;
    warmup) warmup ;;
    *) echo "Usage: $0 {start|stop|restart|status|health|warmup}"; exit 1 ;;
esac
'''
        return script.replace("REPLACE_REPO_ID", repo_id)

    def render_anchors_yaml(self) -> str:
        return """anchors:
  strong:
    files:
      - "agent.md"
      - "session.md"
      - "skill.md"
      - "prime.md"
      - "readme.md"
      - "readme_tf.md"
      - "context_pack.json"
    dirs:
      - "docs/"
      - "src/"
      - "_ctx/"
      - "tests/"
      - "configs/"
      - ".ai/"
    exts:
      - ".md"
      - ".py"
      - ".json"
      - ".yaml"
      - ".sh"
    symbols_terms:
      - "class"
      - "def"
      - "import"
      - "from"
      - "return"
  weak:
    intent_terms:
      - "template"
      - "example"
      - "how-to"
      - "runbook"
      - "doc"
      - "docs"
      - "documentación"
      - "protocolo"
      - "configuración"
      - "implementación"
    doc_terms:
      - "guía"
      - "manual"
      - "uso"
      - "cómo"
      - "how"
      - "howto"
      - "why"
      - "what"
      - "dónde"
      - "where"
"""

    def render_aliases_yaml(self) -> str:
        return """aliases:
  - phrase: "session persistence"
    add_anchors: ["session.md", "session append"]
  - phrase: "ciclo search-get"
    add_anchors: ["ctx search", "ctx get"]
  - phrase: "persistencia de sesión"
    add_anchors: ["session.md", "session append"]
  - phrase: "cómo usar session"
    add_anchors: ["session.md", "session append"]
  - phrase: "documentación de session"
    add_anchors: ["session.md", "doc"]
  - phrase: "protocolo de sesión"
    add_anchors: ["session.md", "protocolo"]
  - phrase: "crear segmento"
    add_anchors: ["trifecta create", "segment"]
  - phrase: "validar contexto"
    add_anchors: ["ctx validate", "context pack"]
  - phrase: "sincronizar contexto"
    add_anchors: ["ctx sync", "build"]
  - phrase: "agregar evidencia"
    add_anchors: ["session append", "evidence"]
  - phrase: "limpiar repositorio"
    add_anchors: ["git worktree", "hygiene"]
  - phrase: "constitucion agéntica"
    add_anchors: ["AGENTS.md", "leyes"]
  - phrase: "warmup inteligencia"
    add_anchors: ["warmup", "graph index"]
"""

    def render_makefile(self, config: TrifectaConfig) -> str:
        return f'''# {config.segment.replace("-", " ").title()} - F1 Makefile
# Standard Dev Interface for AI Agents & Humans

# Smart binary detection with Capability Check (Graph & AST)
TRIFECTA_BIN := $(shell \
	BIN=$$(command -v trifecta 2> /dev/null); \
	if [ -n "$$BIN" ] && $$BIN graph --help > /dev/null 2>&1; then \
		echo "$$BIN"; \
	else \
		echo "uv run trifecta"; \
	fi)

.PHONY: help sync search status warmup clean doctor check

help:
	@echo "{config.segment.replace("-", " ").title()} - F1 Engine Commands"
	@echo "========================================="
	@echo "make sync          Sync Trifecta context"
	@echo "make search Q='..' Search context"
	@echo "make status        Show daemon & repo status"
	@echo "make warmup        Initialize deep intelligence (LSP/Graph)"
	@echo "make doctor        Run system diagnostics"
	@echo "make check         Run linters (Biome/Pyrefly)"
	@echo "make clean         Purge worktrees and stale state"

sync:
	$(TRIFECTA_BIN) ctx sync --segment .

search:
	@test -n "$(Q)" || (echo "Q='query' is required"; exit 1)
	$(TRIFECTA_BIN) ctx search --segment . --query "$(Q)" --limit 6

status:
	@./scripts/trifecta_manager.sh status

warmup:
	@./scripts/trifecta_manager.sh warmup

doctor:
	$(TRIFECTA_BIN) doctor --repo .

check:
	@if command -v biome >/dev/null 2>&1; then biome check .; else echo "Warning: biome not installed"; fi
	@if command -v pyrefly >/dev/null 2>&1; then pyrefly check .; else echo "Warning: pyrefly not installed"; fi

clean:
	@echo "Cleaning repository hygiene..."
	git worktree prune
	@find . -name "*.inactive" -delete
	@./scripts/trifecta_manager.sh stop
'''

    def render_biome_json(self) -> str:
        return """{{
  "$schema": "https://biomejs.dev/schemas/2.0.0/schema.json",
  "files": {{
    "ignoreUnknown": true
  }},
  "formatter": {{
    "enabled": true,
    "indentStyle": "space",
    "lineWidth": 100
  }},
  "linter": {{
    "enabled": true,
    "rules": {{
      "recommended": true
    }}
  }}
}}
"""

    def render_pyrefly_toml(self) -> str:
        return """# Pyrefly Type-checking Configuration
project-includes = ["**/*.py*"]
project-excludes = ["**/node_modules", "**/__pycache__", "**/*venv/**"]
use-ignore-files = true
python-version = "3.12"
untyped-def-behavior = "check-and-infer-return-type"
"""

    def render_llms_txt(self, config: TrifectaConfig) -> str:
        return f"""# {config.segment.replace("-", " ").title()} - LLM Reference

> Quick reference for agents. See AGENTS.md for governance.

---

## L0: Quick Reference
- **Sync**: `make sync`
- **Search**: `make search Q='query'`
- **Warmup**: `make warmup` (Activate AST/LSP)
- **Status**: `make status`

## Required Reading Order
1. AGENTS.md (Governance)
2. skill.md (Project Rules)
3. _ctx/agent_{config.segment}.md (Tech Stack)
4. _ctx/session_{config.segment}.md (Current Context)

## Stale Fail-Closed Protocol
If `stale_detected=true` or validation fails:
1. STOP immediately.
2. Run: `make sync`.
3. Run: `trifecta ctx validate --segment .`.
4. Continue ONLY if PASS.

---
## Project Structure
- `src/`: Source code
- `.ai/`: Agential infrastructure
- `configs/`: Semantic anchors & aliases
- `_ctx/`: Context pack & telemetry
- `ADR/`: Architecture Decision Records
- `scripts/`: Operational scripts
"""

    def render_adr_template(self) -> str:
        return """# ADR-XXXX: [Title]

## Status
Proposed | Accepted | Superseded

## Context
[What is the problem we are solving?]

## Decision
[What did we decide?]

## Consequences
[What are the pros and cons of this decision?]
"""

    def render_gitignore(self) -> str:
        return """# Trifecta Lifecycle Artifacts
_ctx/generated/
_ctx/logs/
_ctx/telemetry/
.trifecta/
_ctx/trifecta_config.json

# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
.mypy_cache/
.pytest_cache/
.ruff_cache/
.coverage
htmlcov/

# Node
node_modules/
npm-debug.log*

# OS & IDE
.DS_Store
.vscode/
.idea/

# Agential Traces
.ai/traces/
"""

    def render_session_end_hook(self) -> str:
        return r'''#!/bin/bash
# .ai/hooks/session-end-hook.sh - Standard Session Cleanup Hook

set -euo pipefail

echo "[hook] Finalizing session context..."

# Sync context one last time to ensure traceability
make sync > /dev/null 2>&1 || true

# Clean up ephemeral traces older than 1 hour
find .ai/traces -name "*.trace" -mmin +60 -delete 2>/dev/null || true

echo "✅ Session finalized."
'''
