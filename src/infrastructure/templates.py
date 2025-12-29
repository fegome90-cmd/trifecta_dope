"""Template Renderer for Trifecta files."""
from datetime import datetime

from src.domain.models import TrifectaConfig


class TemplateRenderer:
    """Renders Trifecta templates."""

    def render_skill(self, config: TrifectaConfig) -> str:
        return f"""---
name: {config.segment}
description: Use when working on {config.scope}
---

# {config.segment.replace('-', ' ').title()}

## Overview
{config.scope}

**Ubicación**: `{config.repo_root}/{config.segment}/`

## ⚠️ ONBOARDING OBLIGATORIO ⚠️

1. **skill.md** (este archivo) - Reglas y roles
2. **[PRIME](./_ctx/prime_{config.segment}.md)** - Docs obligatorios
3. **[AGENT](./_ctx/agent.md)** - Stack técnico y gates

> NO ejecutes código sin leer los 3 archivos.

## Core Rules
1. **Sync First**: Valida `.env` antes de cambios
2. **Test Locally**: Tests del segmento antes de commit
3. **Read Before Write**: Lee código antes de modificar
4. **Document**: Actualiza `session_{config.segment}.md`

## CRITICAL PROTOCOL: History Persistence
Antes de ejecutar cualquier herramienta, DEBES seguir este estricto orden de operaciones.

1. **GENERA** el historial y resumen de la conversación en formato YAML.
2. **ESCRIBE** (usando `write_file`) este contenido en: `{config.repo_root}/{config.segment}/_ctx/session_{config.segment}.md`
3. **LEE** el contenido que acabas de preparar (o úsalo de tu memoria).
4. **EJECUTA** el script de ingestión de trifecta (ej: `python scripts/ingest_trifecta.py --segment {config.segment}`) pasando ese contenido como el prompt instruction del agente al iniciar tareas.

## Workflow
```bash
cd {config.repo_root}/{config.segment}
# Validar entorno → Ejecutar tests → Hacer cambios → Commitear
```

## Setup

**Python:**
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt  # o: uv pip install -r requirements.txt
```

**Node:**
```bash
npm install  # o: pnpm install
```

## Commands

**Tests:**
```bash
pytest tests/unit/ -v              # Unitarios
pytest tests/unit/test_{config.segment}.py -k "test_name"
pytest --cov=src tests/             # Con coverage
```

**Lint:**
```bash
# Python
ruff check . --fix && black .
# Node
npm run lint && npm run format
```

## Troubleshooting
| Problema | Solución |
|----------|----------|
| `ImportError` | `pip install -e .` desde repo root |
| `.env` faltante | Copiar desde `.env.example` |
| Lint errors | `ruff check . --fix` o `npm run lint:fix` |
| TypeError | Check versiones de dependencias |

## Integration Points
**Upstream:** <!-- listar -->
**Downstream:** <!-- listar -->
**API:** <!-- contratos si aplica -->

## Resources (On-Demand)
- `@_ctx/prime_{config.segment}.md` - Docs obligatorios
- `@_ctx/agent.md` - Stack y configuración
- `@_ctx/session_{config.segment}.md` - Log de cambios

## LLM Roles
| Rol | Modelo | Uso |
|-----|--------|-----|
| **Worker** | `deepseek-reasoner` | General |
| **Senior** | `claude-sonnet-4-5` | Complejo |
| **Fallback** | `gemini-3.0-flash-preview` | Fallos |

---
**Profile**: `{config.default_profile}` | **Updated**: {config.last_verified}
"""

    def render_prime(self, config: TrifectaConfig, docs: list[str]) -> str:
        # Format docs with priority indicators
        formatted_docs = ""
        if docs:
            for i, doc in enumerate(docs):
                formatted_docs += f"{i+1}. `{doc}`\n"
        else:
            formatted_docs = "<!-- Agregar documentos obligatorios -->"

        return f"""---
segment: {config.segment}
profile: load_only
---

# Prime {config.segment.replace('-', ' ').title()} - Lista de Lectura

> **REPO_ROOT**: `{config.repo_root}`
> Todas las rutas son relativas a esta raíz.
>
> **Orden de lectura**: Fundamentos → Implementación → Referencias

## 🔴 Prioridad ALTA - Fundamentos

**Leer primero para entender el contexto del segmento.**

{formatted_docs}

## 🟡 Prioridad MEDIA - Implementación

<!-- Documentación de implementación específica -->
<!-- Ejemplos: guías de uso, patrones de diseño -->

## 🟢 Prioridad BAJA - Referencias

<!-- Documentación de referencia, archivada -->
<!-- Ejemplos: API docs, especificaciones -->

## 🗺️ Mapa Mental

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

## 📚 Glosario

| Término | Definición |
|---------|------------|
| <!-- Agregar términos clave del segmento --> | <!-- Definiciones breves --> |

## 📝 Notas

- **Fecha última actualización**: {config.last_verified}
- **Mantenedor**: <!-- Agregar si aplica -->
- **Ver también**: [skill.md](../skill.md) | [agent.md](./agent.md)
"""

    def render_agent(self, config: TrifectaConfig) -> str:
        return f"""---
segment: {config.segment}
scope: {config.scope}
repo_root: {config.repo_root}
last_verified: {config.last_verified}
default_profile: {config.default_profile}
---

# Agent Context - {config.segment.replace('-', ' ').title()}

## Source of Truth
| Sección | Fuente |
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
- <!-- Listar dependencias principales de producción -->

**Development:**
- <!-- Listar dependencias de desarrollo -->

## Configuration

**Archivos de configuración:**
```
{config.segment}/
├── .env                    # Variables de entorno (local)
├── .env.example            # Template de variables
├── pyproject.toml          # Config Python (si aplica)
└── package.json            # Config Node (si aplica)
```

**Variables de entorno clave:**
```bash
# Agregar variables específicas del segmento
# Ejemplo:
DATABASE_URL=              # URL de base de datos
API_KEY=                   # Clave de API externa
LOG_LEVEL=info             # Nivel de logging
```

## Gates (Comandos de Verificación)

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
- <!-- ¿Qué módulos/deps necesitas primero? -->

**Downstream Consumers:**
- <!-- ¿Quién usa este segmento? -->

**API Contracts:**
- <!-- Endpoints, funciones, o interfaces expuestas -->

## Architecture Notes

<!-- Patrones de diseño, decisiones arquitectónicas, trade-offs -->

**Design Patterns:**
- <!-- Ej: Repository Pattern, Factory, Observer -->

**Key Decisions:**
- <!-- Por qué se eligió cierta tecnología o enfoque -->

**Known Limitations:**
- <!-- Limitaciones conocidas del segmento -->
"""

    def render_session(self, config: TrifectaConfig) -> str:
        return f"""---
segment: {config.segment}
profile: handoff_log
output_contract:
  append_only: true
  require_sections: [History, NextUserRequest]
  max_history_entries: 10
  forbid: [refactors, long_essays]
---

# Session Log - {config.segment.replace('-', ' ').title()}

## Active Session
- **Objetivo**:
- **Archivos a tocar**:
- **Gates a correr**:
- **Riesgos detectados**:

---

## TRIFECTA_SESSION_CONTRACT
> ⚠️ **Este contrato NO es ejecutado por el sistema en v1.** Es puramente documental.

```yaml
schema_version: 1
segment: {config.segment}
autopilot:
  enabled: true
  debounce_ms: 800
  lock_file: _ctx/.autopilot.lock
  allow_prefixes: ["trifecta ctx "]
  steps:
    - name: build
      cmd: "trifecta ctx build --segment ."
      timeout_sec: 60
    - name: validate
      cmd: "trifecta ctx validate --segment ."
      timeout_sec: 30
```

---

## History
```yaml
# - session:
#     timestamp: "YYYY-MM-DDTHH:MM:SS"
#     user_prompt_summary: ""
#     agent_response_summary: ""
#     files_touched: []
#     outcome: ""
```

---

## Next User Request
<!-- El siguiente agente comienza aquí -->
"""

    def render_readme(self, config: TrifectaConfig) -> str:
        return f"""# {config.segment.replace('-', ' ').title()} - Trifecta Documentation

> **Trifecta System**: Este segmento usa el sistema Trifecta para comprensión rápida por agentes de código.

## 📁 Estructura

```
{config.segment}/
├── readme_tf.md                 # Este archivo - guía rápida
├── skill.md                     # Reglas y contratos (MAX 100 líneas)
└── _ctx/                        # Context resources
    ├── prime_{config.segment}.md # Lista de lectura obligatoria
    ├── agent.md                 # Stack técnico y configuración
    └── session_{config.segment}.md # Log de handoffs (runtime)
```

## 🚀 Flujo de Onboarding (Para Agentes)

1. **Leer `skill.md`** — Reglas, roles, y contratos del segmento
2. **Leer `_ctx/prime_{config.segment}.md`** — Lista de documentos obligatorios
3. **Leer `_ctx/agent.md`** — Stack técnico, configuración, y gates

> [!CAUTION]
> **No ejecutes código sin completar los 3 pasos anteriores.**

## 📊 Perfiles de Output

| Perfil | Propósito | Contract |
|--------|-----------|----------|
| `diagnose_micro` | Máximo texto, código ≤3 líneas | `code_max_lines: 3` |
| `impl_patch` | Patch con verificación | `require: [FilesTouched, CommandsToVerify]` |
| `only_code` | Solo archivos + diff + comandos | `forbid: [explanations]` |
| `plan` | DoD + pasos (sin código) | `forbid: [code_blocks]` |
| `handoff_log` | Bitácora + handoff | `append_only: true` |

## 🔄 Actualización

- **Prime**: Actualizar cuando se agregue/modifique documentación del segmento
- **Session**: Actualizar después de cada handoff entre sesiones
- **Agent**: Revisar cuando cambie el stack técnico o configuración
- **Skill**: Actualizar siguiendo **superpowers:writing-skills** (ver abajo)

## ✏️ Cómo Actualizar skill.md

> **IMPORTANTE**: Al actualizar `skill.md`, seguir el proceso TDD de `writing-skills`

**Referencia obligatoria**: `~/.claude/skills/superpowers/writing-skills/SKILL.md`

**Proceso RED-GREEN-REFACTOR:**
1. **RED**: Crear escenario de presión sin skill - documentar violaciones
2. **GREEN**: Escribir skill que aborde esas violaciones específicas
3. **REFACTOR**: Cerrar loopholes y re-verificar

**Iron Law**: `NO SKILL WITHOUT A FAILING TEST FIRST`

**Estructura recomendada de skill.md:**
```yaml
---
name: {config.segment}
description: Use when working on {config.scope}
---

# {config.segment.replace('-', ' ').title()}

## Overview
<!-- 1-2 sentences describiendo el propósito -->

## When to Use
<!-- Bullet list de síntomas y casos de uso -->

## Core Pattern
<!-- Patrón principal con ejemplos -->

## Common Mistakes
<!-- Errores comunes + cómo evitarlos -->
```

## 📖 Referencias

- **Scope**: {config.scope}
- **Default Profile**: `{config.default_profile}`
- **Last Verified**: {config.last_verified}
- **Repo Root**: `{config.repo_root}`
- **Writing Skills**: `~/.claude/skills/superpowers/writing-skills/SKILL.md`
"""
