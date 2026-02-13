# Plan Completo: WO Gates Hardening (2026-02-13)

## 1) Objetivo
Cerrar Work Orders (WO) de forma determinista, auditable y fail-closed, evitando:
- cierre manual inválido (`running -> done` por `mv`),
- ejecución en root equivocado cuando se usa worktree,
- cierre sin pasar el gate real de verificación (`scripts/verify.sh`).

## 2) North Star Operacional
Un WO solo puede pasar a `done|failed` si se cumple este contrato:
1. Runtime root canónico resuelto (SSOT de estado WO).
2. WO existe en `_ctx/jobs/running/<WO>.yaml`.
3. DoD válido (salvo override explícito de emergencia).
4. `scripts/verify.sh <WO>` ejecutado y exitoso (`exit 0` o `2`).
5. Cierre transaccional (write destino + remove running + remove lock) con rollback.
6. Guardrails de commit bloquean cierres manuales fuera del flujo.

## 3) Estado Actual (implementado)
### 3.1 Implementación ya aplicada
- `scripts/ctx_wo_finish.py`
  - `resolve_runtime_root()` usando git common-dir para worktree safety.
  - `run_verification_gate()` para ejecutar `scripts/verify.sh <WO>`.
  - Detección de corrupción: WO en `done|failed` con `status: running`.
  - Flag de emergencia `--skip-verification`.
- `scripts/prevent_manual_wo_closure.sh`
  - Endurecido: exige transición válida por WO y metadatos de cierre (`status`, `verified_at_sha`, `closed_at`).
- Tests actualizados:
  - `tests/unit/test_wo_finish_validators.py`
  - `tests/unit/test_wo_finish_cli.py`
  - `tests/integration/test_wo_closure.py`
  - `tests/integration/test_sidecar_integration.py`
- Documentación actualizada:
  - `docs/backlog/WORKFLOW.md`
  - `docs/backlog/OPERATIONS.md`

### 3.2 Evidencia actual
- Suite focal WO gates: **PASS**
  - `uv run pytest -q tests/unit/test_wo_finish_cli.py tests/unit/test_wo_finish_validators.py tests/integration/test_wo_closure.py tests/integration/test_sidecar_integration.py`
  - Resultado: `85 passed`

## 4) Brechas Pendientes
1. `scripts/verify.sh` aún no tiene parámetro `--root` explícito para runtime root controlado desde cualquier cwd.
2. `ctx_wo_finish.py` corre `verify.sh`, pero el contrato documental de emergencias debe quedar más explícito en un solo lugar (matriz de overrides).
3. Higiene de estado WO histórico (repositorios con drift previo) requiere corridas de reconciliación y limpieza de artefactos runtime no determinísticos.

## 5) Plan de Ejecución por Fases

### Fase A (P0) — Consolidar contrato de cierre
**Objetivo:** dejar imposible el cierre ambiguo.

Pasos:
1. Añadir `--root` a `scripts/verify.sh` y resolver `runtime_root` de forma canónica.
2. Hacer que `verify.sh` escriba siempre en `_ctx/handoff/<WO>/verification_report.log` del runtime root canónico.
3. Añadir tests de `verify.sh` runtime-root aware (unit/integration shell-level).
4. Actualizar docs operativas con matriz de overrides:
   - `--skip-dod` (emergencia)
   - `--skip-verification` (emergencia)

DoD Fase A:
- `ctx_wo_finish.py` desde worktree y desde repo root produce exactamente el mismo destino de handoff/estado.
- `verify.sh` no depende del cwd para reportar artefactos.

### Fase B (P1) — Higiene y reconciliación de estado
**Objetivo:** limpiar drift acumulado y fijar baseline estable.

Pasos:
1. Ejecutar `ctx_reconcile_state.py` en modo reporte JSON.
2. Corregir manualmente (o con `--apply` controlado) estados inválidos detectados.
3. Validar que no existan WOs en `done/failed` con `status: running`.
4. Remover artefactos runtime del staging técnico (`_ctx/index`, telemetry, etc.) cuando no correspondan al commit.

DoD Fase B:
- Reconcile sin hallazgos críticos (`WO_INVALID_SCHEMA`, `DUPLICATE_WO_ID`, `LOCK_WITHOUT_RUNNING_WO`) o con excepciones documentadas.

### Fase C (P1) — Gate final y merge local seguro
**Objetivo:** integrar sin contaminar `main`.

Pasos:
1. Re-run de tests focales + lint focal Python.
2. Commit técnico atómico del hardening WO gates.
3. Merge local a `main` con revisión de diff scoped (sin runtime noise).
4. Smoke post-merge:
   - `take -> verify -> finish` (done)
   - `take -> verify fail -> finish blocked`

DoD Fase C:
- Flujo happy-path y fail-path reproducibles en local.
- `main` sin archivos runtime accidentales en el commit.

## 6) Gates de Verificación
Comandos mínimos:
1. `uv run pytest -q tests/unit/test_wo_finish_cli.py tests/unit/test_wo_finish_validators.py tests/integration/test_wo_closure.py tests/integration/test_sidecar_integration.py`
2. `uv run ruff check scripts/ctx_wo_finish.py tests/unit/test_wo_finish_cli.py tests/unit/test_wo_finish_validators.py tests/integration/test_wo_closure.py`
3. `bash -n scripts/prevent_manual_wo_closure.sh`
4. `uv run python scripts/ctx_reconcile_state.py --root . --json /tmp/reconcile_wo.json`

## 7) Riesgos y Mitigaciones
- Riesgo: bypass por flags de emergencia.
  - Mitigación: docs explícitas + uso excepcional + evidencia en handoff.
- Riesgo: diferencias de path por symlink/worktree.
  - Mitigación: runtime root canónico + tests de equivalencia `.` vs abs path.
- Riesgo: commits contaminados por runtime artifacts.
  - Mitigación: staging curado estricto por scope.

## 8) Rollback Plan
Si rompe cierre WO:
1. Revert commit de hardening WO gates.
2. Confirmar que `ctx_wo_finish.py` vuelve al comportamiento previo.
3. Mantener hook anti-manual en modo mínimo (no bloquear flujo base).
4. Re-ejecutar tests focales para confirmar restauración.

## 9) Criterio de Cierre de Este Plan
El plan se considera cerrado cuando:
1. Fase A/B/C completadas con evidencia en logs/tests.
2. `main` queda mergeado localmente con diff limpio.
3. No existen hallazgos críticos abiertos en reconciliación WO.

## 10) Registro de ejecución
- Commit hardening aplicado: `5a04aa1`
- Rama actual: `codex/fix-makefile-wo-duplicates`
- Estado: plan operativo actualizado y listo para ejecutar Fase A restante + merge local seguro.
