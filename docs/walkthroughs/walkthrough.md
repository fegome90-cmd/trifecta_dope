# Walkthrough — Trifecta Context Loading refinements (T1–T6)

## Anti-deriva
- **NO UI / NO IDE**: El sistema es 100% CLI y runtime.
- **NO shadow workspace**: Se trabaja sobre el sistema de archivos local directamente.
- **NO rerank cross-encoder**: Uso de scoring léxico y heurístico para latencia mínima.
- **NO indexación global permanente**: Los índices son por segmento y se refrescan bajo demanda.

---

## CLI Contract
Para garantizar consistencia y predictibilidad, se establecen los siguientes flags oficiales:

- **Segmento**: `--segment` (alias `-s`).
- **Presupuesto**: `--budget-token-est` (alias `--budget`).
- **Query**: `--query` (alias `-q`).
- **IDs**: `--ids` (lista separada por comas).
- **Límite (Top-K)**: `--limit` (alias `-k`).
- **Filtro**: `--doc` (`skill`, `prime`, `agent`, `session`) para `ctx search`.

---

## T1 — Plan doc rewrite (Plan A default / Plan B fallback)
**Objetivo**: Establecer la arquitectura de Programmatic Context Calling (Plan A) y Heuristic Full-Files (Plan B).

- **Archivos tocados**:
  - `docs/plans/2025-12-29-trifecta-context-loading.md`
- **Cambios concretos**:
  - **Antes**: Plan contradictorio.
  - **Después**: Plan A (Search + Get + Budget) como estándar. Plan B (Load full files) como fallback explícito.

### Comportamiento de `trifecta load`
- **Por defecto (Macro Plan A)**: Ejecuta internamente `ctx search` + `ctx get` (modo PCC).
- **Fallback Forzado**: `--mode fullfiles` activa Plan B (archivos completos heurísticos).

- **Comandos ejecutables**:
  - **Core (Plan A)**:
    - `trifecta ctx search --segment . --query "locks" --limit 6`
    - `trifecta ctx get --segment . --ids "id1,id2" --mode excerpt --budget-token-est 900`
  - **Fallback/Macro**:
    - `trifecta load --segment . --task "investigate legacy auth" --mode fullfiles`
- **DoD / criterios de aceptación**:
  - Existencia de sección NO-GO.
  - Definición clara de la política "1 search + 1 get" por turno.
  - Semántica de `load` definida: PCC por defecto, Fullfiles bajo demanda.
- **Riesgos mitigados**:
  - **Ambigüedad arquitectónica**: Eliminada al definir roles claros para Plan A y B.
  - **Deriva de alcance**: Mitigada con la sección NO-GO.

---

## T2 — Atomic write + lock
**Objetivo**: Asegurar que la creación del pack de contexto sea atómica y segura ante concurrencia.

- **Archivos tocados**:
  - `src/application/use_cases.py` (`BuildContextPackUseCase`, `ValidateContextPackUseCase`)
- **Cambios concretos**:
  - **Antes**: Escritura directa.
  - **Después**: `AtomicWriter` (tmp->fsync->rename) y lock `_ctx/.autopilot.lock`. Validator profundo.
- **Comandos ejecutables**:
  - `trifecta ctx build --segment .`
  - `trifecta ctx validate --segment .`
- **DoD / criterios de aceptación**:
  - `ctx validate` falla si se cambia un solo carácter de un archivo fuente.
  - Bloqueo concurrente verificado.
- **Riesgos mitigados**:
  - **Corrupción**: Evitada vía escrituras atómicas.

---

## T3 — CLI ctx sync (Macro Fija)
**Objetivo**: Proveer un comando unificado para regenerar el contexto sin lógica compleja.

- **Archivos tocados**:
  - `src/infrastructure/cli.py`
- **Cambios concretos**:
  - **Antes**: Lógica dispersa o inexistente.
  - **Después**: `trifecta ctx sync` ejecuta una macro fija: `ctx build` → `ctx validate`.
  - **Importante**: No parsea `session.md` y no depende de `TRIFECTA_SESSION_CONTRACT`.

- **Comandos ejecutables**:
  ```bash
  trifecta ctx sync --segment .
  # Equivalente a:
  # trifecta ctx build --segment . && trifecta ctx validate --segment .
  ```
- **DoD / criterios de aceptación**:
  - `ctx sync` regenera y valida el pack en un solo paso.
- **Riesgos mitigados**:
  - **Desincronización**: Un solo comando garantiza que el pack esté fresco y válido.

---

## T4 — Budget/backpressure behavior
**Objetivo**: Controlar el consumo de tokens.

- **Archivos tocados**:
  - `src/application/context_service.py`
  - `src/application/use_cases.py`
- **Cambios concretos**:
  - **Antes**: Sin ordenamiento por valor.
  - **Después**: Ordenamiento por Value-per-Token. Truncado inteligente.
- **Comandos ejecutables**:
  - `trifecta ctx get --segment . --ids ID --budget-token-est 400`
- **DoD / criterios de aceptación**:
  - Output incluye nota de advertencia si hubo backpressure.
- **Riesgos mitigados**:
  - **Explosión de tokens**: Controlada.

---

## T5 — session.md contract + watcher thin
**Objetivo**: Documentar el contrato de Autopilot para referencia humana (v1) o futura implementación (v2).

- **Archivos tocados**:
  - `src/application/use_cases.py` (Solo soporte básico, sin motor de lectura de configs).
- **Cambios concretos**:
  - **Runner Externo (Watcher)**: Dispara `trifecta ctx sync` ante cambios (ej: `fswatch -o . | xargs -n1 -I{} trifecta ctx sync --segment .`).
  - **Motor Interno**: NO hay un motor de lectura de configuración en v1. La lógica es fija.

#### Contrato YAML (session.md)
> ⚠️ **Este contrato NO es ejecutado por el sistema en v1.** Es puramente documental o para futuras versiones.

````md
## TRIFECTA_SESSION_CONTRACT
```yaml
schema_version: 1
segment: .
autopilot:
  enabled: true
  debounce_ms: 800
  lock_file: _ctx/.autopilot.lock
  allow_prefixes: ["trifecta ctx "]
  steps:
    - name: build
      cmd: "trifecta ctx build --segment ."
      timeout_sec: 60
    - name: validate
      cmd: "trifecta ctx validate --segment ."
      timeout_sec: 30
```
````

- **DoD / criterios de aceptación**:
  - El YAML existe como referencia pero está marcado explícitamente como NO ejecutable.
  - El sistema funciona sin leer `session.md`.
- **Riesgos mitigados**:
  - **Complejidad innecesaria**: Se evita parsers y lógica de orquestación en v1.

---

## T6 — fullfiles fallback (non-default)
**Objetivo**: Proveer fallback robusto.

- **Archivos tocados**:
  - `src/application/use_cases.py` (`MacroLoadUseCase`)
- **Cambios concretos**:
  - Soporte explícito de `--mode fullfiles`.
- **Comandos ejecutables**:
  - `trifecta load --segment . --task "legacy" --mode fullfiles`
- **DoD / criterios de aceptación**:
  - Carga completa verificada.
- **Riesgos mitigados**:
  - **Inaccesibilidad**: Garantizada continuidad operativa.

---

## Failure Modes (Strict Gates)

| Escenario | Comportamiento del Sistema | Acción Requerida |
| :--- | :--- | :--- |
| **Search sin hits** | Retorna vacío. **NO hace fallback automático** a fullfiles en Plan A. | Usuario debe refinar query o invocar explícitamente `--mode fullfiles`. |
| **Budget Exceeded** | `ctx get` retorna `excerpt` + highlight warning. | Solicitar chunks específicos o aumentar `--budget-token-est`. |
| **Pack Stale/Invalid** | `ctx validate` falla (exit 1). `load` en modo PCC **falla fast** (Fail-Closed). | Ejecutar `trifecta ctx sync` (o build) para regenerar. **NO** usar contextos corruptos. |
| **Pack Missing** | `load` (default) detecta ausencia y cae a Plan B. | Alerta "Pack not found, using heuristics". **Nota**: `ctx search/get` NO hacen fallback; fallan si no hay pack. |
