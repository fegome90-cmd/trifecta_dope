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

## WO Hygiene Toolkit

Scripts para diagnóstico, limpieza y validación del estado de WOs. Ver documentación completa en → **[`docs/backlog/MANUAL_WO.md`](docs/backlog/MANUAL_WO.md)** (ciclo de vida, DoD, troubleshooting) y **[`agents.md`](agents.md)** (quick workflow).

| Script | Rol | Comando rápido |
|--------|-----|----------------|
| `wo_audit.py` | Auditor forense (read-only). 9 finding codes P0–P2 | `uv run python scripts/wo_audit.py --out /tmp/a.json` |
| `ctx_wo_gc.py` | GC de zombie/ghost worktrees. Conservador (no borra dirty sin `--force`) | `uv run python scripts/ctx_wo_gc.py --dry-run` |
| `wo_retention_gc.py` | GC de evidencia antigua (90 días). Solo borra patches hasheados | `uv run python scripts/wo_retention_gc.py --dry-run` |
| `wo_weekly_gate.sh` | Gate semanal CI. Corre auditor + GC, falla si P0 > 0 | `bash scripts/wo_weekly_gate.sh` |
| `ctx_wo_preflight.py` | Validador pre-take (linting + format). Exit 1 si errores | `make wo-preflight WO=WO-XXXX` |
| `ctx_wo_lint.py` | Linter YAML strict. Reglas de schema + semántica | `make wo-lint` |
| `ctx_wo_fmt.py` | Formatter canónico de YAMLs | `make wo-fmt` |
| `wo_verify.sh` | Motor de cierre. Incluye `transition_to_failed()` para prevenir `fail_but_running` | interno vía `ctx_wo_finish.py` |

**Finding codes del auditor** (9 total): `split_brain` P0, `running_without_lock` P0, `ghost_worktree` P0, `fail_but_running` P0, `lock_without_running` P1, `zombie_worktree` P1, `running_without_worktree` P1, `duplicate_yaml` P2, `pending_in_done` P2.

```bash
# Fail CI si se detectan anomalías críticas
uv run python scripts/wo_audit.py --out /tmp/audit.json --fail-on split_brain,fail_but_running
# GC apply (dirty worktrees exportan patch a _ctx/handoff/WO-XXXX/dirty.patch)
uv run python scripts/ctx_wo_gc.py --apply --force
# Retention GC (limpia patches antiguos, protege decision.md)
uv run python scripts/wo_retention_gc.py --apply --days 90
```

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
- Analizando telemetría del CLI (`trifecta telemetry report/chart/health`)
- Gestionando cache de AST persistente (`trifecta ast cache-stats/clear-cache`)
- Buscando en español (sistema Spanish Aliases activo)
- Gestionando Work Orders via `ctx_wo_take.py` / `ctx_wo_finish.py`
- Diagnosticando anomalías de estado de WOs (`wo_audit.py`)
- Limpiando zombie/ghost worktrees (`ctx_wo_gc.py`)
- Validando WOs antes de ejecutarlos (`ctx_wo_preflight.py`)

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
| **Telemetry health** | `trifecta telemetry health -s .` |
| **Generate plan** | `trifecta ctx plan --segment . --task "..."` |
| **Extract symbols (M1)** | `trifecta ast symbols "sym://python/mod/path"` |
| **Extract symbols (persist cache)** | `trifecta ast symbols "sym://python/mod/path" --persist-cache` |
| **View cache stats** | `trifecta ast cache-stats --segment .` |
| **Clear cache** | `trifecta ast clear-cache --segment .` |
| **Chart telemetry** | `trifecta telemetry chart -s . --type hits` |
| **Check git status** | `git status` (before each commit) |

> ℹ️ WO commands → ver sección **WO Hygiene Toolkit** arriba · [`agents.md`](agents.md) · [`docs/backlog/MANUAL_WO.md`](docs/backlog/MANUAL_WO.md)

## Common Mistakes & Zero-Hit Recovery

| Mistake | Fix |
|---------|-----|
| Keywords en lugar de instrucciones → 0 hits | `--query "Find documentation about how to implement X"` |
| Token budget excedido en un solo ctx.get | `--mode excerpt` + `--budget-token-est 900` |
| `ctx validate` falla silenciosamente | STOP → `make ctx-sync` → re-validate |
| Skipping session.md logging | `trifecta session append --segment . --summary "..."` |

**Zero hits?** Pack está en **inglés** → traduce la query. Si sigue en 0: cambia scope (`ctx.search` busca docs/, no `src/`) → usa `trifecta ast symbols "sym://python/mod/..."` para código fuente.

| Herramienta | Busca en | Usa para |
|-------------|----------|----------|
| `ctx.search` | docs/, README, skill.md, _ctx/ | Documentación, guías |
| `ast symbols` | src/ (código Python) | Clases, funciones, módulos |

> Troubleshooting detallado de WOs → **[`docs/backlog/TROUBLESHOOTING.md`](docs/backlog/TROUBLESHOOTING.md)**

---

**Profile**: `impl_patch` | **Updated**: 2026-02-21 | **Verified Against**: CLI v2.0, Makefile, session.md 2026-02-21, `wo_audit.py`, `ctx_wo_gc.py`, `ctx_wo_preflight.py`, `ctx_wo_lint.py`, `ctx_wo_fmt.py`, `wo_verify.sh` (transactional fix)
