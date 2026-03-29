# Batch 2D — Plan de diseño/SSOT para superficies runtime

> **Estado operativo (2026-03-27):** `docs/adr/ADR-004-runtime-surface-ssot.md` es ahora la **única autoridad soberana** para Batch 2D runtime SSOT/ownership. Este plan queda subordinado a ADR-004 y pierde inmediatamente en cualquier conflicto.
>
> **Sin fallback:** no usar este plan, reportes, handoffs, checklists ni checkpoints como autoridad alternativa. Si algo aquí no coincide con ADR-004, detenerse y re-anclar en ADR-004 antes de seguir.
>
> **Nota de vigencia:** las tareas de “elegir artefacto” y “crear ADR” ya quedaron satisfechas por `ADR-004` y por `docs/reports/2026-03-27-runtime-surface-ssot-evidence.md`; el uso vigente de este plan es solo como contexto derivado e histórico para mantener coherencia documental.
> **Rol derivado:** workflow aid, not authority.

> **Para el siguiente agente:** usar este plan solo como framing histórico subordinado a `ADR-004`; no tratarlo como checklist activo ni ejecutarlo paso a paso.

**Objetivo:** Mantener coherencia documental subordinada a `ADR-004` para las superficies runtime entre `src/platform/*` y `src/trifecta/platform/*`, sin aplicar bugfixes ni patches de runtime en esta fase.

**Arquitectura:** La decisión arquitectónica ya quedó capturada en `ADR-004`. Este plan conserva framing, orden de lectura y guardrails derivados; no redefine la decisión ni autoriza un SSOT alternativo.

**Stack / superficie:** Markdown en `docs/`, artifacts de handoff/checkpoint, ADRs existentes, inspección puntual y de solo lectura de `src/platform/*` y `src/trifecta/platform/*`.

## Estado histórico ya resuelto

- ✅ `ADR-004` ya fijó la decisión soberana de runtime SSOT/ownership.
- ✅ `docs/reports/2026-03-27-runtime-surface-ssot-evidence.md` ya cubre el soporte breve previsto para esta fase.
- ✅ La selección de artefacto principal/apoyo quedó cerrada; las tareas de ejecución que siguen se conservan como **registro histórico**, no como instrucciones activas.

## Alcance y no-objetivos

### Sí entra en alcance
- decidir el artefacto canónico para capturar la decisión (ADR)
- ordenar la lectura mínima de artifacts ya existentes
- dejar explícitos criterios para reabrir un cambio de código más adelante
- documentar riesgos y stop conditions

### No entra en alcance
- **no** editar `src/platform/runtime_manager.py`
- **no** editar `src/trifecta/platform/runtime_manager.py`
- **no** reabrir Batch 2D como bugfix
- **no** alinear firmas, tipos o comportamiento runtime sin evidencia nueva de consumidores activos

## Decisión de artefacto (histórico resuelto)

### Artefacto principal elegido
- **Crear ADR en `docs/adr/`**
- Motivo: el problema actual es de **autoridad/SSOT y ownership arquitectónico** entre dos superficies runtime superpuestas. Eso debe resolverse con una decisión explícita y durable, no con un parche aislado ni con una spec de comportamiento.

### Artefacto de apoyo (condicional)
- **Crear reporte corto en `docs/reports/`** solo si los reportes mencionados en el handoff siguen ausentes o no son reutilizables.
- Motivo: el ADR no debería cargar evidencia operativa extensa; si falta esa evidencia, conviene consolidarla antes en un reporte breve y luego referenciarlo desde el ADR.

### Artefactos descartados en esta fase
- **spec**: prematura hasta decidir primero cuál superficie será canónica
- **ticket/WO de implementación**: secundario; solo después del ADR si todavía queda trabajo ejecutable
- **patch de código**: fuera de alcance

## Tarea 1: Congelar baseline y confirmar límites (histórico resuelto)

**Leer:**
- `_ctx/checkpoints/2026-03-27/checkpoint_132457_batch-2d-runtime-manager-ssot-handoff.md`
- `_ctx/handoff/handoff_2026-03-27_batch-2d-runtime-manager-ssot-design.md`
- `_ctx/handoff/next-agent-checklist_2026-03-27_batch-2d-runtime-manager-ssot-design.md`
- `docs/plans/2026-03-26-lsp-daemon-followup-batches.md`
- `docs/plans/adr-002-platform-runtime.md`
- `docs/adr/ADR-003-required-flow-evolution.md`

**Consultar solo si hace falta anclar nombres/superficies:**
- `src/platform/runtime_manager.py`
- `src/trifecta/platform/runtime_manager.py`
- `src/application/daemon_use_case.py`
- `src/platform/daemon_manager.py`
- `src/platform/health.py`

**Paso 1:** Verificar que el estado de partida siga siendo documental y no de bugfix.

**Paso 2:** Verificar explícitamente si existen o no estos artifacts citados en el handoff:
- `docs/reports/2026-03-26-daemon-drift-code-audit.md`
- `docs/reports/2026-03-26-lsp-daemon-comprehensive-review.md`

**Paso 3:** Registrar en el ADR/report futuro la frase de guardrail:
- "En esta fase no se edita `src/platform/runtime_manager.py` ni `src/trifecta/platform/runtime_manager.py` salvo evidencia nueva y verificable de consumidores activos."

**Verificación:**
```bash
git status --short
for f in \
  docs/reports/2026-03-26-daemon-drift-code-audit.md \
  docs/reports/2026-03-26-lsp-daemon-comprehensive-review.md; do
  test -e "$f" && echo "FOUND $f" || echo "MISSING $f"
done
```

**Resultado esperado:**
- baseline documental confirmado
- reportes faltantes clasificados como `FOUND` o `MISSING`
- ninguna edición en `src/platform/` ni `src/trifecta/platform/`

## Tarea 2: Consolidar evidencia mínima si sigue faltando soporte (histórico resuelto)

**Crear (solo si sigue faltando evidencia reutilizable):**
- `docs/reports/2026-03-27-runtime-surface-ssot-evidence.md`

**Contenido mínimo del reporte:**
- resumen de que `src/platform/runtime_manager.py` y `src/trifecta/platform/runtime_manager.py` no tienen consumidores activos según la evidencia ya levantada
- lista de superficies operativas reales mencionadas por el handoff (`src/application/daemon_use_case.py`, `src/platform/daemon_manager.py`, `src/platform/health.py`)
- nota explícita de que la divergencia actual es de ownership/SSOT, no de bugfix inmediato
- referencia al checkpoint/handoff y al plan histórico `docs/plans/2026-03-26-lsp-daemon-followup-batches.md`

**Paso 1:** Crear el reporte solo si los reportes previos citados siguen ausentes o son insuficientes.

**Paso 2:** Mantener el reporte breve: evidencia, alcance, no-goals, referencias.

**Verificación:**
```bash
test -f docs/reports/2026-03-27-runtime-surface-ssot-evidence.md && sed -n '1,120p' docs/reports/2026-03-27-runtime-surface-ssot-evidence.md
```

**Resultado esperado:**
- existe un soporte citable para el ADR sin tocar código
- el reporte deja claro que no hay justificación actual para patch de runtime

## Tarea 3: Redactar el ADR de autoridad runtime (histórico resuelto)

**Crear:**
- `docs/adr/ADR-00X-runtime-surface-ssot.md`  
  > Reemplazar `00X` por el siguiente número disponible en `docs/adr/`.

**Referenciar desde el ADR:**
- `docs/plans/2026-03-27-batch-2d-runtime-ssot-design-plan.md`
- `docs/plans/2026-03-26-lsp-daemon-followup-batches.md`
- `docs/reports/2026-03-27-runtime-surface-ssot-evidence.md` (si fue creado)
- checkpoint/handoff de `_ctx/`

**Contenido mínimo del ADR:**
- **Contexto:** hay dos superficies runtime (`src/platform/*` vs `src/trifecta/platform/*`) sin autoridad explícita
- **Estado actual:** `runtime_manager` no es consumidor activo ni fuerza convergencia hoy
- **Decisión:** elegir una superficie canónica o, si todavía falta evidencia, declarar una decisión temporal con estado `Proposed`
- **Consecuencias:** qué queda congelado, qué queda deprecado/documentado y qué trabajo futuro podría abrirse
- **No-goal explícito:** no editar `src/platform/runtime_manager.py` ni `src/trifecta/platform/runtime_manager.py` en esta fase
- **Trigger de reapertura:** solo si aparece evidencia nueva de consumidores activos o un requerimiento funcional real

**Paso 1:** Revisar numeración vigente en `docs/adr/`.

**Paso 2:** Redactar el ADR con status `Proposed` o `Accepted` según la fuerza real de la evidencia documental disponible.

**Paso 3:** Si la autoridad no puede decidirse con evidencia suficiente, dejar una decisión intermedia válida:
- congelar el área como "sin autoridad consolidada"
- prohibir patches opportunistas
- abrir explícitamente un trabajo posterior de decisión o migración

**Verificación:**
```bash
ls docs/adr/ADR-*.md
sed -n '1,220p' docs/adr/ADR-00X-runtime-surface-ssot.md
```

**Resultado esperado:**
- existe una decisión durable y citable
- el problema deja de vivir como ambigüedad implícita en handoffs
- sigue sin haber cambios en código runtime

## Tarea 4: Abrir seguimiento solo si el ADR deja trabajo remanente (histórico resuelto)

**Crear (solo si el ADR deja trabajo ejecutable posterior):** una referencia de seguimiento documental, una nota en backlog o un WO, pero **solo después** del ADR.

**Opciones válidas:**
- `docs/backlog/...` si el seguimiento debe vivir en repo
- Work Order nuevo si ya existe alcance ejecutable y verificable
- no crear nada adicional si el ADR resuelve completamente el cierre documental

**Paso 1:** revisar si el ADR deja una migración concreta, deprecación formal o cleanup futuro.

**Paso 2:** si no hay alcance ejecutable, no abrir ticket por inercia.

**Verificación:**
- el seguimiento existe solo si hay un siguiente paso real y delimitado
- no se crea trabajo ficticio para "alinear" runtime sin consumidor activo

## Tarea 5: Cierre y verificación doc-only (histórico de cierre)

**Verificar:**
```bash
git diff --stat
git diff -- docs/adr docs/reports docs/plans _ctx

git diff -- src/platform/runtime_manager.py src/trifecta/platform/runtime_manager.py
```

**Resultado esperado:**
- diffs solo en artifacts documentales
- diff vacío en `src/platform/runtime_manager.py`
- diff vacío en `src/trifecta/platform/runtime_manager.py`

## Criterios de verificación global

- el resultado principal de la tarea es un **ADR**, no un patch
- si faltaba soporte, existe además un **reporte corto** que consolida la evidencia
- el plan histórico `docs/plans/2026-03-26-lsp-daemon-followup-batches.md` sigue siendo referencia histórica y no vuelve a ser checklist activo
- queda escrito, en al menos un artefacto durable, que `runtime_manager.py` no debe editarse en esta fase sin nueva evidencia de consumidores activos
- cualquier trabajo posterior queda explícitamente separado del cierre documental de Batch 2D

## Riesgos

- **Riesgo de scope creep:** que el ADR derive en una implementación inmediata.  
  **Mitigación:** mantener el ADR como decisión arquitectónica y exigir evidencia nueva antes de abrir patch.

- **Riesgo de evidencia incompleta:** los reportes citados en handoff siguen ausentes.  
  **Mitigación:** crear el reporte corto de evidencia antes del ADR.

- **Riesgo de falsa equivalencia:** tratar divergencia de superficies como bugfix automático.  
  **Mitigación:** exigir consumidor activo + fallo observable antes de cualquier cambio de código.

- **Riesgo de contaminar trabajo ajeno:** hay artifacts `_ctx/handoff/*` no rastreados en el worktree.  
  **Mitigación:** ignorarlos; no renombrar, no limpiar, no reescribir.

## Stop conditions

Detenerse inmediatamente si ocurre cualquiera de estas condiciones:

- aparece presión por editar `src/platform/runtime_manager.py` o `src/trifecta/platform/runtime_manager.py` sin evidencia nueva y verificable de consumidores activos
- la discusión deriva hacia fix de firmas, tipos o comportamiento runtime en vez de resolver ownership/SSOT
- la evidencia mínima no alcanza para sostener un ADR ni siquiera en estado `Proposed`
- el trabajo requiere salir del worktree aislado o mezclar cambios con `main` sucio/divergente

## Secuencia recomendada (histórica)

1. Confirmar baseline documental y límites de no-implementación.
2. Verificar ausencia/presencia de reportes citados.
3. Si falta soporte, crear `docs/reports/2026-03-27-runtime-surface-ssot-evidence.md`.
4. Crear `docs/adr/ADR-00X-runtime-surface-ssot.md` como artefacto principal.
5. Solo si el ADR deja trabajo real, abrir seguimiento separado.
6. Cerrar con verificación doc-only y diff vacío en runtime code.

## Resultado esperado de esta fase

Batch 2D queda operacionalizado como **tarea de diseño/SSOT** con una salida documental clara: ADR como SSOT de la decisión, soporte de evidencia solo si hace falta, y prohibición explícita de tocar `runtime_manager` mientras no exista nueva evidencia que convierta el problema en un cambio de comportamiento real.
