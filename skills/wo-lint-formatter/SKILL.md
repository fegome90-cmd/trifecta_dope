---
name: wo-lint-formatter
description: Use when working with Work Orders in trifecta_dope and you need to lint, format, or enforce WO integrity gates in local workflows, CI, or WO take/finish operations.
---

# WO Lint Formatter

## Overview
Aplicar un flujo fail-closed para Work Orders (WO): formatear, validar contratos y bloquear avance de WOs inválidos antes de mover estado.

## Quick Workflow
1. Ejecutar formato determinista:
```bash
make wo-fmt
```
2. Verificar que no queden cambios de formato:
```bash
make wo-fmt-check
```
3. Validar reglas estrictas de WO:
```bash
make wo-lint
```
4. Generar evidencia JSON para CI/auditoría:
```bash
make wo-lint-json > _ctx/telemetry/wo_lint.json
```

## Focused Lint (WO puntual)
Usar validación focalizada para un solo WO cuando se depura creación/toma:
```bash
uv run python scripts/ctx_wo_lint.py --strict --json --wo-id WO-XXXX --root .
```

Interpretar salida:
- `severity=ERROR`: bloqueante.
- `severity=INFO` o no error: no bloqueante.
- Exit code `1`: hay errores.
- Exit code `0`: sin errores bloqueantes.

## Gate in WO Take
Para `scripts/ctx_wo_take.py`, la validación inmediata debe correr antes de lock/worktree/mutaciones de estado:
1. Cargar WO y validar schema básico.
2. Ejecutar lint focalizado con `--wo-id` en modo `--strict --json`.
3. Si hay `ERROR`, abortar con `exit 1` y hints de remediación.

Regla operativa:
- `--force` nunca bypass de integridad (schema/lint).
- `--force` solo puede mantener bypass de validaciones de dependencia de dominio ya existentes.

## Findings To Prioritize
Resolver primero hallazgos que rompen contratos del sistema:
- `id` distinto al nombre de archivo.
- IDs duplicados entre estados.
- `status` inconsistente con carpeta (`pending/running/done/failed`).
- `epic_id` o `dod_id` inexistente.
- `scope.allow`/`scope.deny` faltantes.
- `verify.commands` vacío en `pending`/`running`.
- `dependencies` apuntando a WO inexistente.

## Expected Paths
- WOs: `_ctx/jobs/{pending,running,done,failed}/WO-*.yaml`
- Backlog: `_ctx/backlog/backlog.yaml`
- DoD catalog: `_ctx/dod/*.yaml`
- CI telemetry artifact: `_ctx/telemetry/wo_lint.json`

## Troubleshooting
- Si `wo-fmt-check` falla: ejecutar `make wo-fmt` y revisar diff.
- Si `wo-lint` falla: corregir errores por código de finding antes de reintentar.
- Si `ctx_wo_take.py` rechaza un WO: ejecutar lint focalizado con `--wo-id` para ver errores precisos.

## Verification Before Completion
Antes de cerrar cambios en WOs o scripts WO:
```bash
make wo-fmt-check
make wo-lint
uv run pytest -q tests/unit/test_ctx_wo_lint.py tests/unit/test_ctx_wo_take.py
```
