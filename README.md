# Trifecta Generator

> **North Star**: Un agente entienda cualquier segmento del repo en <60 segundos leyendo solo 3 archivos + 1 log.

# Trifecta — Programming Context Calling (para agentes de código)

## Qué somos
Trifecta es un **sistema de “Programming Context Calling”** diseñado para **agentes que trabajan con código**.  
Tratamos el **contexto como una herramienta**: el runtime entrega al agente **un set pequeño, curado y versionado** de “context-tools” (p. ej. `prime`, `agent`, `session`, `skill`) para que el agente actúe con **disciplina, trazabilidad y bajo costo cognitivo**.

## A qué apuntamos
- **Reducir fricción**: que el agente no pierda tiempo explorando árboles de carpetas ni “adivinando” arquitectura/estado.
- **Operación repetible**: decisiones basadas en artefactos (`prime_*.md`, `agent_*.md`, `session_*.md`, `skill.md`), no en improvisación.
- **Evidencia y auditoría**: cada paso tiene soporte (qué se consultó, por qué y con qué versión).
- **Control**: presupuesto de contexto, políticas de escalada y límites explícitos.

## Qué solucionamos
- “Deep dive” innecesario por el repo para entender por dónde empezar.
- Alucinación de arquitectura/stack/estado por falta de guía explícita.
- Sesiones donde se repite trabajo porque no existe un **estado de sesión** confiable.
- Contextos inflados y caóticos que degradan el rendimiento del agente (“todo el repo al prompt”).
- Falta de procedimiento: el agente no sabe “qué hacer ahora” y deriva.

## NO SOMOS (explícito y no negociable)
**Trifecta NO ES un RAG genérico.**  
No es un buscador global del repositorio ni un sistema que “indexa todo el código” para maximizar recall.

**Trifecta NO ES una base vectorial / embeddings-first por defecto.**  
No depende de vectorizar `src/` ni de “buscar trozos” como estrategia primaria.

**Trifecta NO ES “chat con memoria” ni un notebook de notas.**  
No pretende almacenar conocimiento libre o conversaciones; opera con artefactos curados y versionables.

**Trifecta NO ES una excusa para explorar carpetas a ciegas.**  
El agente no debe recorrer 3 niveles de directorios para “entender” el repo: usa `prime` y la sesión.

**Trifecta NO ES un sistema de recuperación indiscriminada de contexto.**  
El objetivo no es “traer más texto”, es **activar el contexto correcto** como si fuera una tool.

## Principio operativo
**Meta-first, código on-demand.**  
El agente inicia con `skill → prime → agent → session`.  
Solo escala a código cuando es estrictamente necesario y siguiendo rutas/contratos curados.

## Función de cada markdown (sin mezclar audiencias)
- `README.md`: onboarding humano del proyecto y quickstart.
- `CLAUDE.md`: contrato operativo para Claude Code.
- `AGENTS.md`: contrato operativo para otros runtimes/agentes.
- `skill.md`: runbook operativo del segmento (reglas + ciclo Search/Get + gates).
- `llms.txt`: resumen corto para carga rápida por LLM.
- `_ctx/agent_trifecta_dope.md`: estado técnico activo (features/gates/stack).
- `_ctx/prime_trifecta_dope.md`: lista de lectura priorizada.
- `_ctx/session_trifecta_dope.md`: bitácora append-only de handoff.

## Problema

Los agentes de código (Claude, Gemini, Codex) todavía pueden perder tiempo recorriendo demasiado código o consumiendo contexto irrelevante cuando no existe un workflow curado de contexto, sesión y verificación.

## Solución

Trifecta mantiene un workflow operativo explícito para que agentes y humanos trabajen con:

- contexto curado (`skill`, `prime`, `agent`, `session`)
- contexto recuperable bajo demanda (`ctx search/get`)
- evidencia de sesión append-only
- validación fail-closed del context pack
- superficies técnicas explícitas para daemon / LSP / AST / repo registry

---

## Estado actual del repo

Este repositorio ya no es solo un “generator” mínimo. Hoy agrupa varias superficies activas:

- **CLI principal** (`src/infrastructure/cli.py`)
- **Context Pack / PCC** (`src/application/*`, `src/domain/*`, `trifecta ctx ...`)
- **Daemon / LSP** (`src/platform/daemon_manager.py`, `src/application/daemon_use_case.py`, `src/infrastructure/daemon/`, `src/infrastructure/lsp_client.py`)
- **Repo registry / status / doctor / telemetry**
- **Artefactos de contexto del segmento** (`skill.md`, `_ctx/agent_trifecta_dope.md`, `_ctx/prime_trifecta_dope.md`, `_ctx/session_trifecta_dope.md`)

## 🏗️ Arquitectura actual (alto nivel)

```
trifecta_dope/
├── src/
│   ├── domain/           # contratos, modelos, naming, políticas
│   ├── application/      # use cases y orquestación
│   ├── infrastructure/   # CLI, adapters, renderers, LSP client, daemon internals
│   ├── platform/         # daemon manager, health, registry/runtime contracts
│   └── cli/              # helpers de presentación / tarjetas / errores
├── tests/                # unit + integration
├── README.md
├── skill.md
└── _ctx/
    ├── agent_trifecta_dope.md
    ├── prime_trifecta_dope.md
    └── session_trifecta_dope.md
```

### Capas y responsabilidades

| Capa | Responsabilidad | Ejemplos |
|------|-----------------|----------|
| **Domain** | contratos y modelos puros | `segment_resolver.py`, `lsp_contracts.py` |
| **Application** | casos de uso y coordinación | `daemon_use_case.py`, `status_use_case.py`, `search_get_usecases.py` |
| **Infrastructure** | CLI, adapters, implementación concreta | `cli.py`, `lsp_client.py`, `daemon/runner.py` |
| **Platform** | lifecycle shell, runtime/registry, health | `daemon_manager.py`, `health.py`, `registry.py` |

### Principios activos

1. `uv` es el runner canónico para desarrollo y validación
2. El context pack se trata como herramienta operativa, no como RAG indiscriminado
3. `session` es append-only
4. Los workflows de review (`branch-review`, `reviewctl`) deben ejecutarse desde branch/worktree limpio
5. Cambios documentales deben reflejar el estado real del repo, no inventar capacidades

---

## Estructura Trifecta (Output)

```
<segment-name>/
├── README.md                               # Guía rápida del segmento
├── skill.md                                # Runbook operativo del agente
└── _ctx/
    ├── prime_<segment-name>.md             # Lista de lectura priorizada
    ├── agent_<segment-name>.md             # Estado técnico activo
    └── session_<segment-name>.md           # Log de handoff (append-only)
```

### Archivos

| Archivo | Propósito | Líneas aprox |
|---------|-----------|--------------|
| `README.md` | Onboarding humano | ~50-120 |
| `skill.md` | Reglas, contratos, workflow operativo | ≤100 |
| `prime_*.md` | Lista de lectura obligatoria | ~20-80 |
| `agent_*.md` | Stack técnico, gates, notas activas | ~80-180 |
| `session_*.md` | Bitácora de handoffs | Append-only |

## Perfiles de Output

El sistema usa perfiles (nvim-style modeline) para definir contratos de output:

| Profile | Propósito | Contract |
|---------|-----------|----------|
| `diagnose_micro` | Máximo texto, código ≤3 líneas | `code_max_lines: 3` |
| `impl_patch` | Patch con verificación | `require: [FilesTouched, CommandsToVerify]` |
| `only_code` | Solo archivos + diff + comandos | `forbid: [explanations]` |
| `plan` | DoD + pasos (sin código) | `forbid: [code_blocks]` |
| `handoff_log` | Bitácora + handoff | `append_only: true` |

## Progressive Disclosure

| Nivel | Trigger | Tokens |
|-------|---------|--------|
| **L0** | Score < 0.6 | ~50 (solo frontmatter) |
| **L1** | Score 0.6-0.9 | ~500-1000 (skill completo) |
| **L2** | Score > 0.9 | ~200-500 (resources) |

## Uso

### Quickstart actual

```bash
# Instalar dependencias
uv sync --all-groups

# Ver comandos disponibles
uv run trifecta --help

# Sincronizar contexto del repo actual
uv run trifecta ctx sync --segment .
uv run trifecta ctx validate --segment .

# Buscar y recuperar contexto
uv run trifecta ctx search --segment . --query "daemon"
uv run trifecta ctx get --segment . --ids "<chunk-id>" --mode excerpt
```

### Alias opcional
Si prefieres usar `trifecta` sin prefijo `uv run`:

```fish
alias trifecta="/Users/felipe_gonzalez/.local/bin/uv --directory /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope run trifecta"
```

### Comandos comunes del repo

```bash
# Estado general
uv run trifecta status --help
uv run trifecta doctor --help

# Contexto
uv run trifecta ctx --help
uv run trifecta session --help

# AST / daemon
uv run trifecta ast --help
uv run trifecta daemon --help
```

### Context Pack (PCC)

El **Context Pack** permite al agente:
1. descubrir chunks (`ctx search`)
2. recuperar evidencia exacta (`ctx get`)
3. operar con presupuesto y validación explícita

```bash
uv run trifecta ctx build --segment /path/to/segment
uv run trifecta ctx sync --segment /path/to/segment
uv run trifecta ctx validate --segment /path/to/segment
```

> `ctx sync` es el macro recomendado para build + validate en trabajo diario.

**Estructura del Context Pack:**

```json
{
  "schema_version": 1,
  "segment": "debug_terminal",
  "created_at": "2025-12-29T15:47:37.502279Z",
  "digest": [           // Siempre en prompt (~10-30 líneas)
    {"doc": "skill", "summary": "...", "source_chunk_ids": [...]}
  ],
  "index": [            // Siempre en prompt (referencias)
    {"id": "skill:a1b2...", "title_path": [...], "preview": "...", "token_est": 150}
  ],
  "chunks": [           // Entregado bajo demanda vía tool
    {"id": "skill:a1b2...", "text": "...", "source_path": "..."}
  ]
}
```

**Cómo funciona:**

1. **Prompt base** incluye solo `digest` + `index` (referencias)
2. **Agente llama** `ctx.get --ids X` cuando necesita evidencia específica
3. **Sistema entrega** chunks dentro del presupuesto (budget-aware)
4. **Agente cita** evidencia con `[chunk_id]`

**El agente decide qué cargar, cuándo y con qué presupuesto. NO es recuperación automática.**

> Ver [`docs/plans/2025-12-29-context-pack-ingestion.md`](./docs/plans/2025-12-29-context-pack-ingestion.md) para especificación completa.

## 🔧 Mini-RAG (Herramienta de Desarrollo)

> **NOTA**: Mini-RAG es una herramienta **externa** para que TÚ (desarrollador) consultes  
> la documentación del CLI. **NO es parte del paradigma Trifecta.**

Trifecta usa búsqueda lexical (grep-like), NO embeddings.

### Setup (solo para desarrollo del CLI)

```bash
# Desde la raíz del proyecto
make minirag-setup MINIRAG_SOURCE=~/Developer/Minirag
make minirag-chunk
make minirag-index
```

### Consultas

```bash
make minirag-query MINIRAG_QUERY="PCC"
```

> El índice usa `.mini-rag/chunks/**/*.md` (generados) y `knowledge/**/*.pdf` definidos en
> `.mini-rag/config.yaml`.

**Para agentes**: Usar `trifecta ctx search`, NO Mini-RAG.

## Instalación

```bash
cd trifecta_dope
uv sync --all-groups
```

## Verificación recomendada

```bash
# Suite general
uv run pytest tests/ -v

# Lint / tipos
uv run ruff check src tests
uv run mypy src --no-error-summary

# Contexto
uv run trifecta ctx sync --segment .
uv run trifecta ctx validate --segment .
```

## Desarrollo

```bash
# Ayuda general del CLI
uv run trifecta --help

# Ayuda de subcomandos
uv run trifecta ctx --help
uv run trifecta daemon --help
uv run trifecta ast --help
```

## 🐛 Debugging Scripts

Scripts de utilidad para debugging de componentes LSP y daemon:

| Script | Propósito |
|--------|-----------|
| `debug_client.py` | Debug LSP Client (lifecycle, state transitions) |
| `debug_status.py` | Debug LSP Daemon (status checks) |
| `debug_ts.py` | Test tree-sitter parser initialization |

### Uso

```bash
# Desde el root del proyecto (requiere venv activo)
.venv/bin/python scripts/debug/debug_client.py
.venv/bin/python scripts/debug/debug_status.py
.venv/bin/python scripts/debug/debug_ts.py
```

> **Nota**: Estos scripts asumen que el proyecto está instalado en modo editable (`uv sync`).

## Referencias

- [`docs/braindope.md`](./docs/braindope.md) - Especificación completa del sistema
- [`writing-skills`](../.claude/skills/superpowers/writing-skills/) - Metodología para crear SKILL.md

## Roadmap

### CLI & Templates
- [x] Especificación completa (braindope.md)
- [x] Clean Architecture implementation
- [x] CLI con comandos `create`, `validate`, `refresh-prime`
- [x] README.md automático en cada segmento
- [x] Enhanced templates (skill, agent, prime) con ejemplos concretos
- [x] CLI UX improvements: validación, errores contextuales, dry-run
- [x] Fish shell completions

### Context Pack
- [x] Context Pack ingestion script (token-optimized)
- [x] Schema v1 con digest + index + chunks
- [x] Fence-aware chunking (respeta bloques de código)
- [x] Digest determinista (scoring system)
- [x] IDs estables (normalized hash)
- [x] E2E tests (34 tests passing)

### Pending
- [ ] Prueba con segmentos reales (`debug_terminal`, `hemdov`, `eval`)
- [ ] MCP Discovery Tool para activación automática
- [ ] Progressive Disclosure (L0/L1/L2) en hooks

---

## 🛠️ Best Practices & Troubleshooting

### 1. Reglas de Oro para Operación Multi-Workspace
*   **Target Segment**: Usa siempre `--segment /path/to/target`. El flag `--path` está deprecado para comandos `ctx` y `load`.
*   **Validar PCC**: Si quieres usar Plan A (búsqueda inteligente), verifica que exista `segment/_ctx/context_pack.json`. Si no existe, corre `trifecta ctx build --segment ...`.

### 2. Depuración de Búsqueda (0 Hits)
Si `trifecta load` cae a fallback cuando no debería:
1.  **Diagnóstico**: Ejecuta `trifecta ctx search --segment Path --query "keyword"`.
2.  **Causa**: Si retorna vacío, tus palabras clave no están en el índice.
3.  **Solución**:
    *   Agrega los documentos relevantes a `segment/_ctx/prime_*.md`.
    *   Regenera el índice: `trifecta ctx build --segment Path`.

### 3. Rutas Hardcoded
El CLI imprime lo que lee. Si ves rutas extrañas en el output de `load`, provienen de los archivos del segmento (`prime`, `agent`, `skill`), no del CLI. Edita los archivos del segmento para corregirlas.
