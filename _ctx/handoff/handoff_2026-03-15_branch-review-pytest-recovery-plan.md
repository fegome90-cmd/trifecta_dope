# Handoff: branch-review pytest recovery plan

**Fecha**: 2026-03-15 09:15
**Sesión**: Branch Review Recovery Prep

---

## Resumen Ejecutivo

Se completó la fase de preparación para continuar el branch review fallido con un flujo controlado y sin ejecutar todavía cambios sobre el entorno Python.

El run afectado es `run_20260315_f32c9328` y su estado operativo actual es:
- `ruff`: `PASS`
- `pytest`: `FAIL`
- agentes requeridos completos: `code-reviewer`, `code-simplifier`, `pr-test-analyzer`
- frontend gate: `SKIP` por `.reviewctl/project-gates.json`

El bloqueo restante no es un fallo funcional del código revisado sino un problema de provisión del entorno de `pytest`: la colección aborta por imports faltantes reportados como `typer`, `yaml` y `pydantic`.

---

## Trabajo Ya Hecho

### 1. Descubrimiento de skills
Se usó `skill-hub` en la terminal para buscar las skills más apropiadas para continuar este trabajo.

Skills seleccionadas:
- `branch-review`
- `systematic-debugging`
- `python-testing`
- `verification-loop`

### 2. Validación del workflow del repo
Se confirmaron las referencias locales para el flujo de `reviewctl`:
- `docs/reviewctl-agent-guide.md`
- `docs/reviewctl-quick-reference.md`

Hallazgos relevantes:
- `ruff` debe ejecutarse con `bun run lint:ruff`
- el frontend gate sigue deshabilitado
- la fuente de verdad canónica del verdict es `_ctx/review_runs/<run-id>/final.json`

### 3. Plan validado antes de ejecutar
Se definió y validó con el usuario un plan de 6 fases:
1. Confirmar el contrato del run activo
2. Diagnosticar el entorno Python exacto usado por `uv run pytest`
3. Provisionar solo las dependencias faltantes en ese entorno
4. Rerun del `pytest` dirigido e ingest de la nueva salida
5. Regenerar el verdict canónico
6. Verificar consistencia entre `final.json` y `final.md`

---

## Blocker Actual

### pytest gate aborta en collection

**Síntoma**:
El target list generado para `pytest` no puede empezar a ejecutar porque faltan dependencias Python en el entorno activo.

**Dependencias reportadas como faltantes**:
- `typer`
- `yaml`
- `pydantic`

**Interpretación actual**:
Antes de instalar nada, hace falta confirmar dos cosas:
1. cuál es exactamente el intérprete/entorno que usa `uv run pytest`
2. cuál es el target list exacto que el run generó y espera reingestar

---

## Reglas de Ejecución Para El Siguiente Agente

1. No instalar paquetes antes de confirmar el `RUN_ID`, el `plan.json`, el target list y el intérprete real de `uv`.
2. No ampliar el scope de `pytest`; usar solo el target list asociado al run.
3. No cambiar código de producción durante el diagnóstico del entorno.
4. No usar instalaciones globales; cualquier provisión debe caer en el mismo entorno que usa `uv run pytest`.
5. No cerrar el trabajo hasta que `final.json` y `final.md` queden alineados tras `verdict`.

---

## Archivos Clave

- `docs/reviewctl-agent-guide.md`
- `docs/reviewctl-quick-reference.md`
- `.reviewctl/project-gates.json`
- `pyproject.toml`
- `package.json`
- `_ctx/review_runs/<run-id>/plan.json`
- `_ctx/review_runs/<run-id>/final.json`
- `_ctx/review_runs/<run-id>/final.md`

---

## Verificación Esperada

El trabajo solo se considera resuelto si se cumple todo esto:

1. `pytest` deja de abortar por paquetes faltantes.
2. La salida nueva de `pytest` se ingesta correctamente en `reviewctl`.
3. `bun "$REVIEW_CLI" verdict` regenera el estado canónico.
4. `ruff` se mantiene en `PASS`.
5. `final.json` y `final.md` muestran el mismo verdict y los mismos estados para `ruff`, `pytest` y los agentes requeridos.

---

## Para El Siguiente Agente

**Prompt sugerido**:
```
Retoma la recuperación del branch review para run_20260315_f32c9328.

Primero confirma el contrato del run activo en _ctx/review_runs/<run-id>/plan.json y final.json, incluyendo required statics y required agents.
Después recupera el target list exacto de pytest y confirma qué intérprete usa uv run pytest.

No instales dependencias hasta verificar esas dos cosas.
Luego provisiona solo los paquetes faltantes en ese mismo entorno uv, rerun pytest, ingesta la salida, rerun verdict y valida consistencia entre final.json y final.md.
```

---

**Checkpoint**: `_ctx/checkpoints/2026-03-15/checkpoint_091500_branch-review-pytest-recovery-plan.md`
**Bundle**: no generado; `cm-save` no se ejecutó en esta sesión