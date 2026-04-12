# Plan de Corrección de Deuda Técnica: Daemon + LSP

**Fecha**: 2026-03-22
**Alcance**: Todos los issues identificados (Fase 1-3 + preexistentes)
**Política**: No dejamos deuda técnica

---

## 1. Issues de implementación Fase 1-3

### 1.1 Health score cambio de escala (m1)

**Archivo**: `src/platform/health.py`
**Problema**: 3 checks → 2 checks. Score cambió de 0/33/66/100 a 0/50/100.
**Corrección**: Tests que asumen 3 checks deben actualizarse.
**Artefactos**: `tests/` — buscar assertions sobre health score o check count.

### 1.2 Telemetry import ya corregido (m2)

**Estado**: ✅ Resuelto. Import redundante eliminado.

### 1.3 DEFAULT_TTL ya corregido

**Estado**: ✅ Resuelto. Unificado a 300s.

### 1.4 runtime.db ya corregido

**Estado**: ✅ Resuelto. Eliminado del health check.

---

## 2. Issues preexistentes de Pyrefly/Ruff

### 2.1 eval_plan — "Cannot index into int"

**Archivo**: `src/infrastructure/cli.py` líneas ~1209-1240
**Problema**: Pyrefly detecta que `results` contiene `dict | int | Any` por mala inferencia de tipos.
**Causa raíz**: `results` se inicializa como `results = []` y se llena con `results.append({"task_id": i, "task": task, "result": result})`. Pyrefly no puede inferir que todos los elementos son dicts.
**Corrección**: Agregar type annotation explícita: `results: list[dict[str, Any]] = []`
**Artefactos**: `src/infrastructure/cli.py` función `eval_plan()`

### 2.2 typer.core import

**Archivo**: `src/infrastructure/cli.py` línea 60
**Problema**: `typer.core.TyperGroup` usado sin import explícito.
**Corrección**: Cambiar `typer.core.TyperGroup` por `typer.TyperGroup` si está disponible, o agregar import explícito.
**Artefactos**: `src/infrastructure/cli.py` clase `TrifectaGroup`

---

## 3. Issues de tests pendientes

### 3.1 Tests de health con 2 checks

**Buscar**: `tests/` — assertions sobre `checks["db_accessible"]` o score 33/66
**Corrección**: Actualizar assertions para reflejar 2 checks.

### 3.2 Tests de daemon con LSPClient

**Buscar**: `tests/integration/test_lsp_daemon.py`, `tests/unit/test_cli_hardening.py`
**Corrección**: Verificar que tests pasan con nuevo daemon_run que importa LSPClient.

---

## 4. Orden de corrección

| Prioridad | Issue | Tipo | Tiempo estimado |
|-----------|-------|------|-----------------|
| P0 | eval_plan type annotation | Preexistente | 5 min |
| P0 | typer.core import | Preexistente | 2 min |
| P1 | Health score tests | Fase 2 | 10 min |
| P1 | Daemon tests con LSPClient | Fase 3 | 15 min |
| P2 | Verificar todos los tests pasan | Global | 10 min |

---

## 5. Estado

| Issue | Estado |
|-------|--------|
| m1: Health score | Pendiente (tests) |
| m2: Telemetry import | ✅ Resuelto |
| DEFAULT_TTL | ✅ Resuelto |
| runtime.db | ✅ Resuelto |
| eval_plan types | Pendiente |
| typer.core | Pendiente |
| Health tests | Pendiente |
| Daemon tests | Pendiente |
