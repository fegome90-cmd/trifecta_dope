# Trifecta Generator

> **North Star**: Un agente entienda cualquier segmento del repo en <60 segundos leyendo solo 3 archivos + 1 log.

# Trifecta — Programming Context Calling (para agentes de código)

## Qué somos
Trifecta es un **sistema de “Programming Context Calling”** diseñado para **agentes que trabajan con código**.  
Tratamos el **contexto como una herramienta**: el runtime entrega al agente **un set pequeño, curado y versionado** de “context-tools” (p. ej. `prime`, `agent`, `session`, `skill`) para que el agente actúe con **disciplina, trazabilidad y bajo costo cognitivo**.

## A qué apuntamos
- **Reducir fricción**: que el agente no pierda tiempo explorando árboles de carpetas ni “adivinando” arquitectura/estado.
- **Operación repetible**: decisiones basadas en artefactos (`prime.md`, `agent.md`, `session.md`, `skill.md`), no en improvisación.
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
- `agents.md`: contrato operativo para otros runtimes/agentes.
- `skill.md`: runbook operativo del segmento (reglas + ciclo Search/Get + gates).
- `llms.txt`: resumen corto para carga rápida por LLM.
- `_ctx/agent_trifecta_dope.md`: estado técnico activo (features/gates/stack).
- `_ctx/prime_trifecta_dope.md`: lista de lectura priorizada.
- `_ctx/session_trifecta_dope.md`: bitácora append-only de handoff.

## Problema

Los agentes de código (Claude, Gemini, Codex) parsean miles de líneas de código innecesariamente, consumen contexto, y terminan con información obsoleta o incompleta.

## Solución

El sistema **Trifecta** proporciona una estructura estandarizada de **5 archivos** que permite:

- **Comprensión rápida**: <60 segundos para entender un segmento
- **Contexto eficiente**: Solo carga lo necesario (progressive disclosure)
- **Mantenimiento simple**: Estructura predecible, sin drift
- **Onboarding automático**: README con guía para nuevos agentes

---

## 🏗️ Arquectura del Generador

> **⚠️ IMPORTANTE**: Este generador ya está implementado con Clean Architecture. No recrear desde cero.

```
trifecta_dope/
├── src/
│   ├── domain/           # Entidades de negocio (Pydantic models)
│   │   ├── models.py     # TrifectaConfig, TrifectaPack, ValidationResult
│   │   └── constants.py  # MAX_SKILL_LINES, etc.
│   │
│   ├── application/      # Use cases (lógica de negocio)
│   │   └── use_cases.py  # Create, Validate, RefreshPrime
│   │
│   └── infrastructure/   # Implementaciones concretas
│       ├── cli.py        # Typer CLI (entrypoint)
│       ├── templates.py  # TemplateRenderer (markdown generation)
│       └── file_system.py # FileSystemAdapter (disk I/O)
│
├── tests/                # Unit tests (pytest)
├── braindope.md          # Especificación completa
└── README.md             # Este archivo
```

### Capas (Clean Architecture)

| Capa | Responsabilidad | Archivos clave |
|------|-----------------|----------------|
| **Domain** | Modelos de datos, validadores | `models.py`, `constants.py` |
| **Application** | Casos de uso, orquestación | `use_cases.py` |
| **Infrastructure** | CLI, templates, I/O | `cli.py`, `templates.py`, `file_system.py` |

### Flujo de Creación

```
CLI (cli.py)
    ↓
CreateTrifectaUseCase (use_cases.py)
    ↓
TemplateRenderer.render_{skill,prime,agent,session,readme}
    ↓
FileSystemAdapter.save_trifecta
    ↓
5 archivos en disco
```

### Reglas de Diseño

1. **Domain** → sin dependencias externas (solo Pydantic)
2. **Application** → solo depende de Domain
3. **Infrastructure** → implementa interfaces de Application/Domain
4. **Templates** → f-strings, sin Jinja2 (simplicidad)

### Extensiones

Para agregar un nuevo comando:

1. Crear use case en `application/use_cases.py`
2. Agregar comando en `infrastructure/cli.py`
3. Agregar tests en `tests/test_use_cases.py`

---

## Estructura Trifecta (Output)

```
<segment-name>/
├── README.md                              # Guía rápida del segmento
├── skill.md                               # Reglas (MAX 100 líneas)
└── _ctx/
    ├── prime_<segment-name>.md            # Lista de lectura
    ├── agent.md                           # Stack técnico
    └── session_<segment-name>.md          # Log de handoff (runtime)
```

### Archivos

| Archivo | Propósito | Líneas aprox |
|---------|-----------|--------------|
| `README.md` | Guía rápida + onboarding | ~50-80 |
| `skill.md` | Reglas, contratos, workflows | ≤100 |
| `prime_*.md` | Lista de lectura obligatoria | ~50-100 |
| `agent.md` | Stack técnico, dependencies | ~100-150 |
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

### 1. Alias (Recomendado)
Para usar `trifecta` desde cualquier carpeta sin instalarlo globalmente:

```fish
# Agregar a ~/.config/fish/config.fish
alias trifecta="<REPO_ROOT>/.local/bin/uv --directory <REPO_ROOT>/Developer/agent_h/trifecta_dope run trifecta"
```

Luego:
```bash
cd ~/Developer/AST
trifecta ctx build .
```

### 2. Ejecución Directa (Sin Alias)
```bash
# Desde cualquier directorio
uv --directory ~/Developer/agent_h/trifecta_dope run trifecta load --path ~/Developer/AST --segment ast --task "Fix bug"
```

### 3. Autocompletado (Fish)
Para tener autocompletado nativo en todos los comandos:

```bash
mkdir -p ~/.config/fish/completions
ln -s $(pwd)/completions/trifecta.fish ~/.config/fish/completions/trifecta.fish
source ~/.config/fish/completions/trifecta.fish
```

### Generar Trifecta (Ejemplos)
```bash
# Crear trifecta para un segmento
trifecta create --segment eval-harness --path eval/eval-harness/ --scan-docs eval/docs/

# Validar trifecta existente
trifecta validate --path eval/eval-harness/
```

### Generar Context Pack (Programming Context Calling)

El **Context Pack** es un índice estructurado que permite al agente:
1. Descubrir qué chunks existen (`ctx.search`)
2. Invocar chunks específicos (`ctx.get --ids X`)
3. Operar con presupuesto estricto (budget-aware)

**Analogía**: Como "Tool Search Tool" de Anthropic, pero para contexto.

```bash
# Comando oficial (recomendado)
trifecta ctx build --segment /path/to/segment

# Validar integridad
trifecta ctx validate --segment /path/to/segment
```

> **DEPRECADO**: `scripts/ingest_trifecta.py` será removido en v2.  
> Usar solo para debugging interno del CLI.

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
uv sync
```

### Multi-Segment Installation

Para instalar contexto en múltiples segmentos del repositorio, usa el script estable:

```bash
# Script recomendado (Clean Architecture compliant)
uv run python scripts/install_FP.py --segment /path/to/segment1 --segment /path/to/segment2

# DEPRECATED: scripts/install_trifecta_context.py (backward compatibility only)
```

El script `install_FP.py` utiliza validadores desde `src/infrastructure/validators.py` y sigue principios de Clean Architecture.

## Tests

```bash
uv run pytest tests/ -v
```

## Desarrollo

```bash
# Ejecutar CLI con Typer
uv run typer src/infrastructure/cli.py run create --help
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
