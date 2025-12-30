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

### Stale Fail-Closed Protocol

If `ctx validate` fails or `stale_detected=true`:
- STOP immediately
- Run: `trifecta ctx sync --segment .` + `trifecta ctx validate --segment .`
- Log: "Stale: true -> sync+validate executed"
- Continue ONLY if PASS

## Common Mistakes
- Skipping session logging
- Using absolute paths outside segment
- Continuing with stale pack
- Silent fallback to Plan B

## Resources (On-Demand)
- `@_ctx/prime_{config.segment}.md` - Reading list
- `@_ctx/agent.md` - Tech stack & gates
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

> **REPO_ROOT**: `{config.repo_root}`
> Todas las rutas son relativas a esta raiz.
>
> **Orden de lectura**: Fundamentos -> Implementacion -> Referencias

## [HIGH] Prioridad ALTA - Fundamentos

**Leer primero para entender el contexto del segmento.**

{formatted_docs}

## [MED] Prioridad MEDIA - Implementacion

<!-- Documentacion de implementacion especifica -->
<!-- Ejemplos: guias de uso, patrones de disenio -->

## [LOW] Prioridad BAJA - Referencias

<!-- Documentacion de referencia, archivada -->
<!-- Ejemplos: API docs, especificaciones -->

## [MAP] Mapa Mental

```mermaid
mindmap
  root({config.segment})
    <!-- Agregar conceptos clave del segmento -->
    <!-- Ejemplo:
    Fundamentos
    Arquitectura
    Componentes
    Interfaces
    -->
```

## [DICT] Glosario

| Termino | Definicion |
|---------|------------|
| <!-- Agregar terminos clave del segmento --> | <!-- Definiciones breves --> |

## [NOTE] Notas

- **Fecha ultima actualizacion**: {config.last_verified}
- **Mantenedor**: <!-- Agregar si aplica -->
- **Ver tambien**: [skill.md](../skill.md) | [agent.md](./agent.md)
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
| Providers | `hemdov/src/hemdov/infrastructure/config/providers.yaml` |

## Tech Stack
<!-- Lenguajes, frameworks, y herramientas principales -->

**Lenguajes:**
- <!-- Ej: Python 3.11+, TypeScript 5.x -->

**Frameworks:**
- <!-- Ej: FastAPI, React, Pydantic -->

**Herramientas:**
- <!-- Ej: pytest, ruff, uv, npm -->

## Dependencies

**Runtime:**
- <!-- Listar dependencias principales de produccion -->

**Development:**
- <!-- Listar dependencias de desarrollo -->

## Configuration

**Archivos de configuracion:**
```
{config.segment}/
|-- .env                    # Variables de entorno (local)
|-- .env.example            # Template de variables
|-- pyproject.toml          # Config Python (si aplica)
|__ package.json            # Config Node (si aplica)
```

**Variables de entorno clave:**
```bash
# Agregar variables especificas del segmento
# Ejemplo:
DATABASE_URL=              # URL de base de datos
API_KEY=                   # Clave de API externa
LOG_LEVEL=info             # Nivel de logging
```

## Gates (Comandos de Verificacion)

**Unit Tests:**
```bash
# Python
pytest tests/unit/ -v

# Node/TypeScript
npm test
# o
jest tests/unit/
```

**Integration Tests:**
```bash
# Python
pytest tests/integration/ -v

# Node
npm run test:integration
```

**Linting:**
```bash
# Python
ruff check .
black --check .

# Node
npm run lint
```

**Type Checking:**
```bash
# Python (mypy)
mypy src/

# TypeScript
npm run type-check
```

**Build:**
```bash
# Python
pip install -e .

# Node
npm run build
```

## Integration Points

**Upstream Dependencies:**
- <!-- Que modulos/deps necesitas primero? -->

**Downstream Consumers:**
- <!-- Quien usa este segmento? -->

**API Contracts:**
- <!-- Endpoints, funciones, o interfaces expuestas -->

## Architecture Notes

<!-- Patrones de disenio, decisiones arquitectonicas, trade-offs -->

**Design Patterns:**
- <!-- Ej: Repository Pattern, Factory, Observer -->

**Key Decisions:**
- <!-- Por que se eligio cierta tecnologia o enfoque -->

**Known Limitations:**
- <!-- Limitaciones conocidas del segmento -->

"""

    def render_session(self, config: TrifectaConfig) -> str:
        return f"""# session.md - Trifecta Context Runbook

segment: {config.segment}

## Purpose
This file is a **runbook** for using Trifecta Context tools efficiently:
- progressive disclosure (search -> get)
- strict budget/backpressure
- evidence cited by [chunk_id]

## Quick Commands (CLI)
```bash
# SEGMENT="." es valido SOLO si tu cwd es el repo target (el segmento).
# Si ejecutas trifecta desde otro lugar (p.ej. desde el repo del CLI), usa un path absoluto:
# SEGMENT="/abs/path/to/AST"
SEGMENT="."

# Usa un termino que exista en el segmento (ej: nombre de archivo, clase, funcion).
# Si no hay hits, refina el query o busca por simbolos.
trifecta ctx sync --segment "$SEGMENT"
trifecta ctx search --segment "$SEGMENT" --query "<query>" --limit 6
trifecta ctx get --segment "$SEGMENT" --ids "<id1>,<id2>" --mode excerpt --budget-token-est 900
trifecta ctx validate --segment "$SEGMENT"
trifecta load --segment "$SEGMENT" --mode fullfiles --task "Explain how symbols are extracted"
```

## Rules (must follow)

* Max **1 ctx.search + 1 ctx.get** per user turn.
* Prefer **mode=excerpt**; use raw only if necessary and within budget.
* Cite evidence using **[chunk_id]**.
* If **validate fails**: stop, rebuild. **No silent fallback**.
* **STALE FAIL-CLOSED**: If `stale_detected=true`, STOP -> `ctx sync` + `ctx validate` -> log "Stale: true -> sync+validate executed" -> continue only if PASS.

## Session Log (append-only)

### Entry Template (max 12 lines)
```md
## YYYY-MM-DD HH:MM - ctx cycle
- Segment: .
- Objective: <que necesitas resolver>
- Plan: ctx sync -> ctx search -> ctx get (excerpt, budget=900)
- Commands: (pending/executed)
- Evidence: (pending/[chunk_id] list)
- Warnings: (none/<code>)
- Next: <1 concrete step>
```

Reglas:
- **append-only** (no reescribir entradas previas)
- una entrada por run
- no mas de 12 lineas

## TRIFECTA_SESSION_CONTRACT (NON-EXECUTABLE in v1)

> Documentation only. Not executed automatically in v1.

```yaml
schema_version: 1
segment: .
autopilot:
  enabled: false
  note: "v2 idea only - NOT executed in v1"
```

## Watcher Example (optional)

```bash
# Ignore _ctx to avoid loops.
fswatch -o -e "_ctx/.*" -i "skill.md|prime.md|agent.md|session.md" . \\
  | while read; do trifecta ctx sync --segment "$SEGMENT"; done
```

## Next User Request

<!-- The next agent starts here -->

"""

    def render_readme(self, config: TrifectaConfig) -> str:
        return f"""# {config.segment.replace("-", " ").title()} - Trifecta Documentation

> **Trifecta System**: Este segmento usa el sistema Trifecta para comprension rapida por agentes de codigo.

## [FILE] Estructura

```
{config.segment}/
|-- readme_tf.md                 # Este archivo - guia rapida
|-- skill.md                     # Reglas y contratos (MAX 100 lineas)
|__ _ctx/                        # Context resources
    |-- prime_{config.segment}.md # Lista de lectura obligatoria
    |-- agent.md                 # Stack tecnico y configuracion
    |__ session_{config.segment}.md # Log de handoffs (runtime)
```

## [CLI] CLI Usage

### Opcion A: alias con TRIFECTA_CLI_ROOT
```bash
export TRIFECTA_CLI_ROOT="/absolute/path/to/trifecta_dope"
alias trifecta='uv --directory "$TRIFECTA_CLI_ROOT" run trifecta'
```

### Opcion B: directo

```bash
uv --directory "$TRIFECTA_CLI_ROOT" run trifecta ctx sync --segment .
uv --directory "$TRIFECTA_CLI_ROOT" run trifecta ctx search --segment . --query "parser" --limit 6
uv --directory "$TRIFECTA_CLI_ROOT" run trifecta load --segment . --mode fullfiles --task "My task"
```

## [GO] Flujo de Onboarding (Para Agentes)

1. **Leer `skill.md`** - Reglas, roles, y contratos del segmento
2. **Leer `_ctx/prime_{config.segment}.md`** - Lista de documentos obligatorios
3. **Leer `_ctx/agent.md`** - Stack tecnico, configuracion, y gates

> [!CAUTION]
> **No ejecutes codigo sin completar los 3 pasos anteriores.**

## [DATA] Perfiles de Output

| Perfil | Proposito | Contract |
|--------|-----------|----------|
| `diagnose_micro` | Maximo texto, codigo <=3 lineas | `code_max_lines: 3` |
| `impl_patch` | Patch con verificacion | `require: [FilesTouched, CommandsToVerify]` |
| `only_code` | Solo archivos + diff + comandos | `forbid: [explanations]` |
| `plan` | DoD + pasos (sin codigo) | `forbid: [code_blocks]` |
| `handoff_log` | Bitacora + handoff | `append_only: true` |

## [SYNC] Actualizacion

- **Prime**: Actualizar cuando se agregue/modifique documentacion del segmento
- **Session**: Actualizar despues de cada handoff entre sesiones
- **Agent**: Revisar cuando cambie el stack tecnico o configuracion
- **Skill**: Actualizar siguiendo **superpowers:writing-skills** (ver abajo)

## [EDIT] Como Actualizar skill.md

> **IMPORTANTE**: Al actualizar `skill.md`, seguir el proceso TDD de `writing-skills`

**Referencia obligatoria**: `~/.claude/skills/superpowers/writing-skills/SKILL.md`

**Proceso RED-GREEN-REFACTOR:**
1. **RED**: Crear escenario de presion sin skill - documentar violaciones
2. **GREEN**: Escribir skill que aborde esas violaciones especificas
3. **REFACTOR**: Cerrar loopholes y re-verificar

**Iron Law**: `NO SKILL WITHOUT A FAILING TEST FIRST`

**Estructura recomendada de skill.md:**
```yaml
---
name: {config.segment}
description: Use when working on {config.scope}
---

# {config.segment.replace("-", " ").title()}

## Overview
<!-- 1-2 sentences describiendo el proposito -->

## When to Use
<!-- Bullet list de sintomas y casos de uso -->

## Core Pattern
<!-- Patron principal con ejemplos -->

## Common Mistakes
<!-- Errores comunes + como evitarlos -->
```

## [REF] Referencias

- **Scope**: {config.scope}
- **Default Profile**: `{config.default_profile}`
- **Last Verified**: {config.last_verified}
- **Repo Root**: `{config.repo_root}`
- **Writing Skills**: `~/.claude/skills/superpowers/writing-skills/SKILL.md`
"""
