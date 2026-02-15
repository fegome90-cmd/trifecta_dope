---
name: trifecta_dope
description: Use when working on Verification
---
## Overview
Verification

## ⚠️ ONBOARDING OBLIGATORIO ⚠️

1. **skill.md** (este archivo) - Reglas y roles
2. **[PRIME](./_ctx/prime_trifecta_dope.md)** - Docs obligatorios
3. **[AGENT](./_ctx/agent_trifecta_dope.md)** - Stack técnico y gates
4. **[SESSION](./_ctx/session_trifecta_dope.md)** - Log de handoffs y estado actual

> NO ejecutes código ni hagas cambios sin leer los 4 archivos.

## Core Rules

1. **make install** - Siempre comienza con `make install` para sincronizar dependencias

2. **Search → Get (Con Instrucciones, NO Keywords)**
   
   ❌ **MAL (keyword):**
   ```bash
   trifecta ctx search --segment . --query "telemetry" --limit 6
   ```
   
   ✅ **BIEN (instrucción):**
   ```bash
   trifecta ctx search --segment . \
     --query "Encuentra documentación sobre cómo implementar el sistema de telemetría con event schema y ejemplos de uso" \
     --limit 6
   ```
   
   Luego: `trifecta ctx get --segment . --ids "id1,id2" --mode excerpt --budget-token-est 900`

3. **Log Evidence** - Registra en `session.md` vía `trifecta session append --segment . --summary "..."`

4. **Test Gates** - Antes de commit: `make gate-all` (Unit + Integration + Acceptance fast)

5. **No Silent Fallback** - Si `ctx validate` falla: STOP → `make ctx-sync` → re-validate

> ⚠️ Violaciones críticas: YAML long history, rutas absolutas, scripts legacy, fallback silencioso, pack stale

---

## Backlog System

**Epic registry**: `_ctx/backlog/backlog.yaml`  
**Work Orders**: `_ctx/jobs/{pending,running,done,failed}/*.yaml`  
**Validate**: `python scripts/ctx_backlog_validate.py --strict`  
**Schema**: `docs/backlog/schema/*.schema.json`

Read `docs/backlog/README.md` for workflow details.

---

### Session Evidence Protocol (The 4-Step Cycle)

```bash
# 1. PERSIST intent
trifecta session append --segment . --summary "<what you'll do>" \
  --files "file1.py,file2.md" --commands "ctx search,ctx get"

# 2. SEARCH with instruction (not keyword)
trifecta ctx search --segment . \
  --query "Find documentation about how to implement the session persistence protocol" \
  --limit 6

# 3. GET excerpt to confirm relevance
trifecta ctx get --segment . --ids "id1,id2" --mode excerpt --budget-token-est 900

# 4. RECORD result
trifecta session append --segment . --summary "Completed: found and reviewed context"
```

Or use **Makefile shortcuts**:
```bash
make install              # Sync dependencies
make ctx-search Q="instruction" SEGMENT=.
make ctx-sync SEGMENT=.
make gate-all            # Full test gate before commit
```

## When to Use

**Use skill.md when:**
- Necesitas sincronizar contexto de un segmento (vía Trifecta CLI)
- Implementando cambios en código/docs del segmento
- Realizando handoff entre sesiones (log en session.md)
- Buscando info específica sin cargar archivos completos (ctx search → ctx get)
- Validando integridad del context pack antes de cambios (ctx validate)
- Trabajando con AST symbols M1 PRODUCTION (`trifecta ast symbols`)
- Analizando telemetría del CLI (`trifecta telemetry report/chart/stats`)
- Gestionando cache de AST persistente (`trifecta ast cache-stats/clear-cache`)

**Triggers to activate:**
- Entraste al workspace sin leer skill.md + prime + agent + session
- El CLI falla con "SEGMENT_NOT_INITIALIZED" Error Card
- `ctx validate` reporta stale pack
- Necesitas buscar documentación sin RAG (solo PRIME index)
- Quieres extraer símbolos de módulos Python sin tree-sitter
- Necesitas verificar estadísticas de cache de AST o limpiar cache persistente

**⚠️ NO usar (experimental/inmaduro):**
- `trifecta obsidian` - Integración no aprobada, en desarrollo

## Core Pattern

### The Context Cycle (Search -> Get)
1. **Search**: Encuentra el `chunk_id` relevante.
2. **Get (Excerpt)**: Lee un resumen/inicio para confirmar relevancia.
3. **Get (Raw)**: Carga el contenido completo solo si es necesario y cabe en el presupuesto.

### Session Persistence

> [!IMPORTANT]
> **Todo** cambio significativo o comando ejecutado **DEBE** ser registrado en `session.md` para mantener la continuidad del agente. Sin esto, el sistema Trifecta es solo un CLI; la persistencia es lo que permite la colaboración multi-agente funcional.

## Quick Reference

| Task | Command |
|------|---------|
| **Install deps** | `make install` |
| **Search docs** | `make ctx-search Q="instruction" SEGMENT=.` |
| **Sync context** | `make ctx-sync SEGMENT=.` |
| **Run tests** | `make gate-all` |
| **Full validation** | `trifecta ctx validate --segment .` |
| **View telemetry** | `trifecta telemetry report -s . --last 30` |
| **Generate plan** | `trifecta ctx plan --segment . --task "..."` |
| **Extract symbols (M1)** | `trifecta ast symbols "sym://python/mod/path"` |
| **Extract symbols (persist cache)** | `trifecta ast symbols "sym://python/mod/path" --persist-cache` |
| **View cache stats** | `trifecta ast cache-stats --segment .` |
| **Clear cache** | `trifecta ast clear-cache --segment .` |
| **Chart telemetry** | `trifecta telemetry chart -s . --type hits` |
| **Check git status** | `git status` (before each commit) |

## Common Mistakes

| Mistake | Why Bad | Fix |
|---------|---------|-----|
| Using keywords instead of instructions | Produce noise/zero-hits | Use `--query "Find documentation about how to implement X"` |
| Exceeding token budget in single ctx.get | Degrades agent attention | Use `--mode excerpt` + budget ~900 tokens max |
| Absolute paths in commands | Not portable, breaks on different machines | Use relative paths or `SEGMENT=.` |
| Ignoring ctx validate failures | Pack may be stale/corrupted | STOP → `make ctx-sync` → re-validate |
| Skipping session.md logging | Lose continuity between agent runs | Always `trifecta session append` after significant work |
| Executing legacy ingestion scripts | Data corruption, duplication | Use `trifecta ctx sync` (official command) |

## Zero-Hit Recovery Protocol

Si `ctx.search` retorna **0 hits**, sigue este protocolo:

### Step 1: Verificar idioma
- El context pack está en **inglés**
- Query en español → traduce a inglés y reintenta
- Ejemplo: "servicio" → "service"

### Step 2: Verificar scope
- `ctx.search` busca en **documentación** (docs/, README, skill.md)
- Para buscar **código fuente** → usa `trifecta ast symbols "sym://python/mod/..."`
- `ctx.search` NO indexa `src/` por diseño

### Step 3: Ampliar query
| Mal (keyword) | Bien (instrucción) |
|---------------|---------------------|
| `"telemetry"` | `"Find telemetry event schema documentation"` |
| `"config"` | `"How to configure segment initialization"` |
| `"error"` | `"Error handling patterns in context pack"` |

### Step 4: Escalar (max 3 intentos)
```
Intento 1 → 0 hits → Refinar query (Step 1-3)
Intento 2 → 0 hits → Cambiar scope (docs → code via ast symbols)
Intento 3 → 0 hits → Usar fallback: `trifecta load --mode fullfiles --task "..."`
```

### Diferencia ctx.search vs ast symbols
| Herramienta | Busca en | Usa para |
|-------------|----------|----------|
| `ctx.search` | docs/, README, skill.md, _ctx/ | Documentación, guías |
| `ast symbols` | src/ (código Python) | Clases, funciones, módulos |

---

**Profile**: `impl_patch` | **Updated**: 2026-02-14 | **Verified Against**: CLI v2.0, Makefile, session.md 2026-02-14, Zero-Hit Analysis Report
