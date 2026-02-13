# Agent Guide: Work Orders (WO) System

Este documento es la guía definitiva para que cualquier agente pueda operar el sistema de Work Orders (WO) en `trifecta_dope` sin errores. **Léelo antes de tocar cualquier YAML en `_ctx/jobs/`.**

---

## 🚀 Workflow Rápido (TL;DR)

1.  **Sync & Search**: `uv run trifecta ctx sync --segment .` → `uv run trifecta ctx search --segment . --query "..."`
2.  **Take**: `uv run python scripts/ctx_wo_take.py WO-XXXX`
3.  **Work**: `cd .worktrees/WO-XXXX` → Implementar → `git commit`
4.  **Handoff (Opcional)**: `uv run python ../../scripts/ctx_wo_finish.py WO-XXXX --generate-only`
5.  **Finish**: `uv run python scripts/ctx_wo_finish.py WO-XXXX`

---

## 🏗️ Arquitectura y Estados

Los WOs viven en `_ctx/jobs/` y se mueven entre carpetas. **NUNCA** muevas archivos manualmente; usa los scripts.

*   `pending/`: WOs listos para ser tomados.
*   `running/`: WOs en ejecución (tienen un `.lock` y un worktree en `.worktrees/`).
*   `done/`: WOs completados con éxito.
*   `failed/`: WOs que fallaron la validación o ejecución.

---

## 📂 Archivos y Rutas Relevantes

### 🗂️ Registro y Estado
*   **Backlog Maestro**: `_ctx/backlog/backlog.yaml`
*   **Catálogo de DoD**: `_ctx/dod/*.yaml`
*   **Work Orders**: `_ctx/jobs/{pending,running,done,failed}/`
*   **Handoffs & Evidencia**: `_ctx/handoff/`

### 📜 Scripts de Orquestación
*   **Take (Asignación)**: `scripts/ctx_wo_take.py`
*   **Finish (Cierre)**: `scripts/ctx_wo_finish.py`
*   **Lint (Validación)**: `scripts/ctx_wo_lint.py`
*   **Format (Formateador)**: `scripts/ctx_wo_fmt.py`
*   **Verify (Gate General)**: `scripts/verify.sh`
*   **Reconcile (Reparación)**: `scripts/ctx_reconcile_state.py`

### 📖 Documentación Extendida
*   **Guía de Uso**: `docs/guides/work_orders_usage.md`
*   **Guía de Workflow**: `docs/backlog/WORKFLOW.md`
*   **Troubleshooting**: `docs/backlog/TROUBLESHOOTING.md`

---

## 🛠️ Herramientas y Comandos Críticos

### 1. Gestión de WOs
*   **Listar Pendientes**: `uv run python scripts/ctx_wo_take.py --list`
*   **Ver Estado**: `uv run python scripts/ctx_wo_take.py --status`
*   **Tomar WO**: `uv run python scripts/ctx_wo_take.py WO-XXXX`
*   **Cerrar WO**: `uv run python scripts/ctx_wo_finish.py WO-XXXX`

### 2. Calidad e Integridad (Fail-Closed)
*   **Linter de WOs**: `make wo-lint` (Valida esquemas, IDs y estados).
*   **Formatter de WOs**: `make wo-fmt` (Aplica formato determinista a los YAMLs).
*   **Check de Formato**: `make wo-fmt-check` (Falla si hay YAMLs sin formatear).
*   **Verification Gate**: `bash scripts/verify.sh` (Ejecuta tests, lint, format y types).

---

## ⚠️ Reglas de Oro para Agentes

1.  **Main Repo Limpio**: No puedes cerrar un WO si el repositorio principal (no el worktree) tiene cambios sin commitear. Si el main está sucio por otro proceso, **espera**.
2.  **Aislamiento Total**: Trabaja **SIEMPRE** dentro de `.worktrees/WO-XXXX`. No mezcles cambios en el repo raíz.
3.  **Commit antes de Finish**: Debes hacer commit de todo tu trabajo dentro del worktree antes de ejecutar `ctx_wo_finish.py`.
4.  **No Bypass**: No uses `--skip-verification` o `--force` a menos que sea una emergencia documentada.
5.  **Evidence is Key**: Al cerrar, el sistema captura el SHA del commit y los logs de tests. Asegúrate de que `verify.commands` en el YAML del WO sea correcto.

---

## 🔍 Troubleshooting Común

*   **"Repository has uncommitted changes"**: Limpia o commitea en el repo raíz. Revisa `git status --porcelain`.
*   **"Lock exists"**: Si el lock en `running/WO-XXXX.lock` tiene más de 1 hora, `ctx_wo_take.py` lo limpiará solo. Si no, verifica si hay otro agente trabajando.
*   **"Schema validation failed"**: Ejecuta `make wo-lint` para ver el error exacto. Probablemente falte un campo o el `id` no coincida con el nombre del archivo.
*   **"Detached HEAD"**: Si entras al worktree y no estás en branch, usa `git checkout feat/wo-WO-XXXX`.

---

## 📋 Definition of Done (DoD)

Cada WO debe cumplir con el DoD especificado en su campo `dod_id` (ver `_ctx/dod/`). Por defecto, `DOD-DEFAULT` exige:
*   Código sin errores de lint (`ruff`).
*   Tests unitarios/integración pasando.
*   Documentación actualizada si aplica.
*   Evidencia en `_ctx/handoff/WO-XXXX/`.

---

*Manual operativo para Agentes - Trifecta Context Engine v2.0*
