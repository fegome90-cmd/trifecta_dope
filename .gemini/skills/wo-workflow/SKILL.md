---
name: wo-workflow
description: Flujo correcto para trabajar con Work Orders (WO) en trifecta_dope. Usar cuando se inicia, ejecuta o cierra un WO. Incluye reglas fail-closed, aislamiento de worktrees, y verificación de estado.
---

# Work Order Workflow

## Overview

El sistema WO proporciona **entornos de desarrollo aislados** usando git worktrees. Cada WO sigue una máquina de estados estricta con verificación automática.

## Antes de Empezar

> ⚠️ Leer [skill.md](../../skill.md) para reglas generales del proyecto.

Contexto obligatorio antes de trabajar en WOs:
1. `skill.md` - Reglas y comandos Trifecta CLI
2. `_ctx/agent_trifecta_dope.md` - Stack técnico y gates activos
3. `_ctx/session_trifecta_dope.md` - Estado actual y handoffs

## Regla de Oro

> **El pipeline es fail-closed.** Si algo está sucio, bloquea. Esto es correcto.

```
Main repo sucio + Worktree limpio → NO PUEDE cerrar WO
```

El script `ctx_wo_finish.py` valida contra el **common dir** (repo principal), no contra el worktree. Esto garantiza auditabilidad.

## State Machine

```
┌─────────┐     ┌─────────┐     ┌──────────┐     ┌─────────┐
│ PENDING │ ──▶ │ RUNNING │ ──▶ │   DONE   │     │ FAILED  │
└─────────┘     └─────────┘     └──────────┘     └─────────┘
                    │
                    │ (stale >1h)
                    ▼
              ┌─────────┐
              │ LOCK    │
              │ CLEANUP │
              └─────────┘
```

## Flujo Completo

### 1. Listar WOs pendientes

```bash
uv run python scripts/ctx_wo_take.py --list
```

### 2. Ver estado del sistema

```bash
uv run python scripts/ctx_wo_take.py --status
```

Muestra:
- Conteo de WOs por estado
- Worktrees activos
- Branches en uso

### 3. Tomar un WO (Pending → Running)

```bash
uv run python scripts/ctx_wo_take.py WO-XXXX
```

**Qué hace automáticamente:**
1. Valida WO con lint fail-closed (`ctx_wo_lint.py --strict`)
2. Crea lock atómico en `_ctx/jobs/running/WO-XXXX.lock`
3. Genera branch `feat/wo-WO-XXXX` desde `main`
4. Crea worktree en `.worktrees/WO-XXXX`
5. Mueve YAML de `pending/` a `running/`

**Si falla:** Revisa `ctx_wo_lint.py` para ver errores de validación.

### 4. Trabajar en el Worktree

```bash
cd .worktrees/WO-XXXX
```

**Estás en un entorno aislado:**
- Branch: `feat/wo-WO-XXXX`
- Working directory separado del main repo
- Git operations normales

**Comandos útiles:**
```bash
# Verificar dónde estás
git rev-parse --show-toplevel
git branch

# Commit del trabajo
git add .
git commit -m "feat(WO-XXXX): descripción del cambio"
```

### 5. Generar artefactos DoD (opcional pero recomendado)

```bash
# Desde el worktree
uv run python ../../scripts/ctx_wo_finish.py WO-XXXX --generate-only
```

Genera en `_ctx/handoff/WO-XXXX/`:
- `tests.log` - Resultado de tests
- `lint.log` - Resultado de linting
- `diff.patch` - Diff del trabajo
- `handoff.md` - Documento de handoff
- `verdict.json` - Veredicto final

### 6. Cerrar WO (Running → Done)

```bash
# Desde cualquier lugar (main o worktree)
uv run python scripts/ctx_wo_finish.py WO-XXXX
```

**Precondiciones OBLIGATORIAS:**
1. ✅ Worktree limpio (commits hechos)
2. ✅ **Main repo limpio** (esto es lo que bloquea frecuentemente)
3. ✅ Artefactos DoD generados
4. ✅ `verify.sh` pasa (o `--skip-verification` para emergencias)

**Si falla con "Repository has uncommitted changes":**

```
TRIFECTA_ERROR_CODE: WO_NOT_RUNNING
CAUSE: Repository has uncommitted changes. Commit or stash before finishing WO.
```

**Diagnóstico:**
```bash
# Verificar main repo
git status --porcelain

# Verificar worktree
cd .worktrees/WO-XXXX && git status --porcelain
```

| Main Repo | Worktree | Resultado |
|-----------|----------|-----------|
| Limpio | Limpio | ✅ Puede cerrar |
| Sucio | Limpio | ❌ Bloqueado (esperar) |
| Limpio | Sucio | ❌ Commit en worktree |
| Sucio | Sucio | ❌ Commit ambos |

**Regla:** Si el main repo tiene trabajo de otro stream, **esperar**. No forzar limpieza.

## Verificación y Gates

> Para lint/format detallado, usar skill [wo-lint-formatter](../wo-lint-formatter/SKILL.md)

### Lint de WOs

```bash
# Lint estricto de todos los WOs
make wo-lint

# Lint de un WO específico
uv run python scripts/ctx_wo_lint.py --strict --wo-id WO-XXXX --root .

# Output JSON para CI
make wo-lint-json
```

### Formato de WOs

```bash
# Check sin modificar
make wo-fmt-check

# Aplicar formato
make wo-fmt
```

### Gate completo (verify.sh)

```bash
bash scripts/verify.sh
```

Incluye: tests, lint, format, type-check, WO hygiene, backlog validation.

## Troubleshooting

### "WO not in running/"

El WO no está en estado RUNNING. Verificar:
```bash
ls _ctx/jobs/running/WO-*.yaml
```

### "Lock exists"

Otro proceso tiene el lock. Verificar:
```bash
cat _ctx/jobs/running/WO-XXXX.lock
```

Si está stale (>1 hora), el sistema lo limpia automáticamente en el próximo take.

### "Detached HEAD"

El worktree está en detached HEAD. Volver a la branch:
```bash
cd .worktrees/WO-XXXX
git checkout feat/wo-WO-XXXX
```

### "Schema validation failed"

El WO tiene formato inválido. Ver contra schema:
```bash
uv run python scripts/ctx_backlog_validate.py --strict
```

## Reconcile State

Si el estado se corrompe (worktrees huérfanos, locks inconsistentes):

```bash
# Diagnóstico
uv run python scripts/ctx_reconcile_state.py --json /tmp/reconcile.json

# Ver findings
cat /tmp/reconcile.json
```

## Scripts Reference

| Script | Propósito |
|--------|-----------|
| `helpers.py` | Utilidades: worktree, lock, branch |
| `ctx_wo_take.py` | Tomar WO (auto branch + worktree) |
| `ctx_wo_finish.py` | Cerrar WO (DoD + verify.sh) |
| `ctx_wo_lint.py` | Validar contratos WO (strict mode) |
| `ctx_wo_fmt.py` | Formatear WO YAMLs |
| `ctx_reconcile_state.py` | Reparar estado inconsistente |
| `ctx_backlog_validate.py` | Validar schemas JSON |

## Resumen de Comandos

```bash
# Ver WOs pendientes
uv run python scripts/ctx_wo_take.py --list

# Tomar WO
uv run python scripts/ctx_wo_take.py WO-XXXX

# Ir al worktree
cd .worktrees/WO-XXXX

# Trabajar y commit
git add . && git commit -m "feat(WO-XXXX): ..."

# Generar artefactos (opcional)
uv run python ../../scripts/ctx_wo_finish.py WO-XXXX --generate-only

# Cerrar WO (requiere main limpio)
uv run python scripts/ctx_wo_finish.py WO-XXXX

# Si main está sucio → esperar, no forzar
```

## Anti-Patterns

❌ **NO hacer:**
- Mover WO YAMLs manualmente
- Usar `--skip-verification` para bypass
- `git commit --no-verify` en WOs
- Borrar worktrees manualmente (`rm -rf`)
- Forzar limpieza del main repo si no es tu trabajo

✅ **SÍ hacer:**
- Usar scripts para transiciones de estado
- Commit work en worktree antes de finish
- Esperar a que main repo esté limpio naturalmente
- Usar `--status` para diagnosticar
- Documentar en handoff.md
