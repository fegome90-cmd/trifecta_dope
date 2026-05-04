# Agent Guide: Work Orders (WO) System

Este documento es la guía operativa para que cualquier agente pueda trabajar con el sistema de Work Orders (WO) en `trifecta_dope` sin romper contratos.

> **Referencia obligatoria:** para la máquina de estados completa, transacciones, locks, DoD y artefactos de handoff, consulta `docs/backlog/MANUAL_WO.md` (Single Source of Truth).  
> Este `AGENTS.md` resume **cómo** debe trabajar un agente día a día.

---

## 🚀 Workflow Rápido (TL;DR)

1. **Sync & Search**: `uv run trifecta ctx sync --segment .` → `uv run trifecta ctx search --segment . --query "..."`
2. **Preflight (OBLIGATORIO)**: `make wo-preflight WO=WO-XXXX`
3. **Take**: `uv run python scripts/ctx_wo_take.py WO-XXXX`
4. **Work**: `cd <REPO_ROOT>/Developer/agent_h/.worktrees/WO-XXXX` → implementar → `git commit`
5. **(Opcional avanzado)**: `uv run python ../../scripts/ctx_wo_finish.py WO-XXXX --generate-only` para previsualizar DoD si el WO lo documenta.
6. **Finish (único cierre válido)**: `uv run python scripts/ctx_wo_finish.py WO-XXXX`

> Nota: el cierre real del WO **siempre** se hace con `ctx_wo_finish.py` como indica `docs/backlog/MANUAL_WO.md`. No muevas YAMLs entre `pending/running/done/failed` a mano.

---

## 🏗️ Arquitectura y Estados

Los WOs viven en `_ctx/jobs/` y se mueven entre carpetas. **NUNCA** muevas archivos manualmente; usa los scripts.

* `pending/`: WOs listos para ser tomados.
* `running/`: WOs en ejecución (tienen un `.lock` y un worktree en `.worktrees/`).
* `done/`: WOs completados con éxito.
* `failed/`: WOs que fallaron la validación o ejecución.

---

## 📂 Archivos y Rutas Relevantes

### 🗂️ Registro y Estado
* **Backlog Maestro**: `_ctx/backlog/backlog.yaml`
* **Catálogo de DoD**: `_ctx/dod/*.yaml`
* **Work Orders**: `_ctx/jobs/{pending,running,d0ne,failed}/`
* **Handoffs & Evidencia**: `_ctx/handoff/`

### 📜 Scripts de Orquestación
* **Take (Asignación)**: `scripts/ctx_wo_take.py`
* **Finish (Cierre)**: `scripts/ctx_wo_finish.py`
* **Lint (Validación)**: `scripts/ctx_wo_lint.py`
* **Format (Formateador)**: `scripts/ctx_wo_fmt.py`
* **Verify (Gate General)**: `scripts/verify.sh`
* **Reconcile (Reparación)**: `scripts/ctx_reconcile_state.py`

### 📖 Documentación Extendida
* **Manual WO (SSOT)**: `docs/backlog/MANUAL_WO.md`
* **Guía de Workflow**: `docs/backlog/WORKFLOW.md`
* **Troubleshooting**: `docs/backlog/TROUBLESHOOTING.md`

---

## 🛠️ Herramientas y Comandos Críticos

### 1. Gestión de WOs
* **Listar Pendientes**: `uv run python scripts/ctx_wo_take.py --list`
* **Ver Estado**: `uv run python scripts/ctx_wo_take.py --status`
* **Tomar WO**: `uv run python scripts/ctx_wo_take.py WO-XXXX`
* **Cerrar WO**: `uv run python scripts/ctx_wo_finish.py WO-XXXX`

### 2. Calidad e Integridad (Fail-Closed)
* **Linter de WOs**: `make wo-lint` (valida esquemas, IDs y estados).
* **Formatter de WOs**: `make wo-fmt` (aplica formato determinista a los YAMLs).
* **Check de Formato**: `make wo-fmt-check` (falla si hay YAMLs sin formatear).
* **Verification Gate**: `bash scripts/verify.sh` (ejecuta tests, lint, format y types).

---

## ⚠️ Reglas de Oro para Agentes

1. **Main repo limpio**: no puedes cerrar un WO si el repositorio principal (no el worktree) tiene cambios sin commitear. Si el main está sucio por otro proceso, **espera**.
2. **Aislamiento total**: trabaja **SIEMPRE** dentro de `.worktrees/WO-XXXX`. No mezcles cambios en el repo raíz.
3. **Commit antes de Finish**: debes hacer commit de todo tu trabajo dentro del worktree antes de ejecutar `ctx_wo_finish.py`.
4. **No bypass**: no uses opciones de bypass ni ejecutes `wo_verify.sh` directamente; todo cierre pasa por `ctx_wo_finish.py` como define `docs/backlog/MANUAL_WO.md`.
5. **Preflight obligatorio**: nunca ejecutes `ctx_wo_take.py` sobre un WO que no haya pasado `make wo-preflight WO=...` en verde.
6. **Evidence is key**: al cerrar, el sistema captura el SHA del commit y los logs de tests. Asegúrate de que `verify.commands` en el YAML del WO sea correcto.

---

## 🔗 Cómo se integra este documento con el CLI

- `scripts/ctx_wo_take.py` muestra este archivo y `docs/backlog/MANUAL_WO.md` en los *Next steps* al tomar un WO.
- `scripts/ctx_wo_finish.py` referencia `docs/backlog/MANUAL_WO.md` y este `AGENTS.md` en los Error Cards cuando hay errores de estado, DoD o gates.
- `scripts/verify.sh` imprime un recordatorio hacia `docs/backlog/MANUAL_WO.md` y `_ctx/jobs/AGENTS.md` cuando se usa con un `WO_ID`.
- El hook `scripts/hooks/prevent_manual_wo_closure.sh` indica explícitamente que los cierres deben hacerse vía `ctx_wo_finish.py` y remite al manual de WOs.

---

## 🔍 Troubleshooting Común

* **"Repository has uncommitted changes"**: limpia o commitea en el repo raíz. Revisa `git status --porcelain`.
* **"Lock exists"**: si el lock en `running/WO-XXXX.lock` tiene más de 1 h, `ctx_wo_take.py` lo limpiará solo. Si no, verifica si hay otro agente trabajando.
* **"Schema validation failed"**: ejecuta `make wo-lint` para ver el error exacto. Probablemente falte un campo o el `id` no coincida con el nombre del archivo.
* **"Detached HEAD"**: si entras al worktree y no estás en branch, usa `git checkout job/WO-XXXX` (o el branch configurado en el YAML del WO).

---

## 📋 Definition of Done (DoD)

Cada WO debe cumplir con el DoD especificado en su campo `dod_id` (ver `_ctx/dod/`). Por defecto, `DOD-DEFAULT` exige:

* Código sin errores de lint (`ruff`).
* Tests unitarios/integración pasando.
* Documentación actualizada si aplica.
* Evidencia en `_ctx/handoff/WO-XXXX/` (ver detalles en `docs/backlog/MANUAL_WO.md`).

---

## 🔄 Flujo de Higiene Post-Merge

Después de completar un WO y hacer merge a main:

```bash
# 1. Push a main
git push origin main

# 2. Remover worktree
git worktree remove .worktrees/WO-XXXX

# 3. Borrar branch mergeado
git branch -d job/WO-XXXX

# 4. Stashes: NUNCA borrar sin permiso explícito
git stash list --date=local  # Mostrar primero
# Solo después de confirmación: git stash clear

# 5. Verificar estado final
git worktree list
git branch -vv
```

---

## 🚨 Reglas Críticas de Seguridad

### Stashes (CRÍTICO)
- **NUNCA** ejecutar `git stash drop` o `git stash clear` sin permiso explícito.
- **SIEMPRE** mostrar `git stash list` antes de cualquier acción.
- **SIEMPRE** sugerir backup si el stash parece importante.
- **Evidencia**: usuario perdió 95.56% de datos por `stash drop` sin permiso.

### Tags de Seguridad
Antes de operaciones de merge masivas:

```bash
git tag -a "pre-merge-$(date +%Y%m%d-%H%M)" -m "Safety snapshot"
git push --tags
```

---

*Manual operativo para Agentes - Trifecta Context Engine v2.0*  
*Última actualización: 2026-02-17*

