# Trifecta Generator

> **North Star**: Un agente entienda cualquier segmento del repo en <60 segundos leyendo solo 3 archivos + 1 log.

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

### Generar Trifecta (CLI)
```bash
# Desde la raíz del repo
cd trifecta_dope

# Crear trifecta para un segmento
uv run python -m src.infrastructure.cli create \
    --segment eval-harness \
    --path eval/eval-harness/ \
    --scan-docs eval/docs/

# Validar trifecta existente
uv run python -m src.infrastructure.cli validate --path eval/eval-harness/

# Actualizar prime (re-escanea docs)
uv run python -m src.infrastructure.cli refresh-prime \
    --path eval/eval-harness/ \
    --scan-docs eval/docs/
```

### Generar Context Pack (Token-Optimized)

El **Context Pack** es un JSON estructurado que permite a los LLMs ingerir documentación de manera eficiente sin cargar textos completos en el prompt.

```bash
# Generar context_pack.json en _ctx/
python scripts/ingest_trifecta.py --segment debug_terminal

# Con repo root personalizado
python scripts/ingest_trifecta.py --segment hemdov --repo-root /path/to/projects

# Output personalizado
python scripts/ingest_trifecta.py --segment eval --output custom/pack.json
```

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

**Para usarlo en un agente:**

1. **Prompt base** incluye solo `digest` + `index`
2. **Tool** `get_context(chunk_id)` devuelve `chunks["text"]` cuando se necesita
3. **Resultado**: Agente entiende el contexto sin quemar tokens

> Ver [`docs/plans/2025-12-29-context-pack-ingestion.md`](./docs/plans/2025-12-29-context-pack-ingestion.md) para especificación completa.

## Mini-RAG (Contexto Local)

Este repo integra Mini-RAG para consultas rápidas sobre la documentación (RAG local).

### Setup (local source)

```bash
# Desde la raíz del proyecto
make minirag-setup MINIRAG_SOURCE=~/Developer/Minirag
make minirag-index
```

### Consultas

```bash
make minirag-query MINIRAG_QUERY="PCC"
```

> El índice usa `docs/**/*.md` y `knowledge/**` definidos en `.mini-rag/config.yaml`.
## Instalación

```bash
cd trifecta_dope
uv sync
```

## Tests

```bash
uv run pytest tests/ -v
```

## Desarrollo

```bash
# Ejecutar CLI con Typer
uv run typer src/infrastructure/cli.py run create --help
```

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
- [ ] Phase 2: SQLite runtime para context packs grandes
