# Fase 6.5 — Curación incremental del corpus de `skill-hub`

## Northstar
Preservar `skill-hub` como adaptador/caso de uso sobre Trifecta.

No se permite en esta fase:
- modificar Trifecta
- crear sistema paralelo
- crear RAG genérico
- tocar producción
- mejorar harness/parser como solución
- agregar infraestructura nueva

## Qué analicé
- reporte de Fase 6
- postmortem de recuperación
- rows/raw outputs del run congelado
- benchmark/dataset
- manifest/aliases/context pack congelados
- planes maestros de CLOOP

## Hallazgo central
Los fails de recuperación útil no apuntan al engine ni al harness.
Apuntan a la superficie de búsqueda del segmento:
- metadocs contaminando el corpus principal
- benchmark parcialmente desalineado con el manifest real
- duplicados/prefijos ruidosos en superficie visible
- aliases insuficientes para planning/review/debugging/work orders

## Decisión metodológica
Aplicar curación por olas separadas.

### Ola 1
Solo:
1. higiene de metadocs
2. reconciliación benchmark ↔ manifest
3. canonización mínima de duplicados obvios

### Ola 2
Solo si Ola 1 queda cerrada:
- aliases mínimos para vocabulario faltante

### Ola 3
Solo si después de Ola 2 siguen fallando queries específicas:
- refuerzo puntual de SKILL.md directamente implicados

## Bloque 1 — Reconciliación benchmark ↔ manifest real
### 1. Qué analizaste
- expected skills del benchmark vs manifest congelado

### 2. Qué evidencia encontraste
Ghost expectations detectados:
- `methodology-workflows`
- `work-order-workflows`
- `root-cause-tracing`
- `examen-code-review-checklist`

Canonicalizable:
- `systematic-debugging` -> `superpowers-systematic-debugging`

### 3. Qué decisión tomaste
- el benchmark **no puede seguir esperando fantasmas como expectativas primarias**
- antes de medir curación, esos nombres deben ser reemplazados, degradados a adjacent, o removidos

### 4. Qué no tocaste y por qué
- no modifiqué todavía el dataset congelado; primero dejé reconciliación explícita auditable

### 5. Qué artefactos dejaste
- `docs/reports/skill_hub_benchmark_manifest_reconciliation.md`

### 6. Estado
- **pass with issues**

## Bloque 2 — Higiene de metadocs (Ola 1)
### 1. Qué analizaste
Contaminantes detectados:
- `prime_skills-hub.md`
- `agent_skills-hub.md`
- `session_skills-hub.md`
- `AGENTS.md`
- `README.md`

### 2. Qué evidencia encontraste
- `q02` fue absorbida por `prime_skills-hub` y `agent_skills-hub`
- `q12` devolvió `AGENTS.md`
- `context_pack.json` confirma que están en la superficie indexable

### 3. Qué decisión tomaste
- decisión recomendada: **excluir los cinco del espacio principal de búsqueda**
- no degradarlos solamente: el problema es de clase documental, no de prioridad leve

### 4. Qué no tocaste y por qué
- no modifiqué todavía el contexto/segmento congelado; primero dejé la decisión causalmente aislada para E1

### 5. Qué artefactos dejaste
- `docs/reports/skill_hub_phase65_metadoc_hygiene.md`

### 6. Estado
- **pass**

## Bloque 3 — Duplicados y naming visible (Ola 1)
### 1. Qué analizaste
- duplicados obvios
- prefijos ruidosos
- entradas canónicas mínimas

### 2. Qué evidencia encontraste
Duplicados/prefijos con valor de curación inmediata:
- `dispatching-parallel-agents`
- `python-testing`
- `tdd-workflow`
- `strategic-compact`
- `learned-pr-feedback-resolution`
- `branch-review-api` vs `examen-branch-review-api`

### 3. Qué decisión tomaste
- canonizar solo duplicados obvios y prefijos con evidencia directa de contaminación
- no hacer renaming masivo en Ola 1

### 4. Qué no tocaste y por qué
- no toqué familias enteras `official-*`, `plugin-*`, `superpowers-*`, `adr-*` salvo donde había evidencia directa y duplicado claro
- no reescribí SKILL.md aún

### 5. Qué artefactos dejaste
- `docs/reports/skill_hub_phase65_canonicalization_minimal.md`

### 6. Estado
- **pass with issues**

## Mini experimento E1 — solo Ola 1
### Scope
Aplicar únicamente:
- reconciliación benchmark ↔ manifest
- exclusión de metadocs del espacio principal
- canonización mínima de duplicados obvios

### Queries foco
- `q02`
- `q12`

### Controles
- `q07`
- `q10`

### Hipótesis
Si el problema dominante en `q02` y `q12` es contaminación del corpus por metadocs y superficie visible ruidosa, entonces la limpieza de Ola 1 debería mejorar `top3_contains_good_candidate` sin necesidad de aliases nuevos.

### Criterios de éxito
- `q02` mejora `top3_contains_good_candidate`
- `q12` mejora `top3_contains_good_candidate`
- `q07` no degrada
- `q10` no degrada
- no aparecen severe false positives nuevos en negativos conocidos

### Abort / no-go para E1
No correr E1 si:
- benchmark sigue esperando ghost names como winners primarios
- metadocs no pueden excluirse ni degradarse limpiamente en el segmento
- canonización mínima no puede representarse sin tocar Trifecta

## Mini experimento E2 — Ola 2
### Precondición
Solo ejecutar E2 si E1 mejora o al menos no degrada.

### Scope
Agregar solo aliases mínimos y acotados para:
- planning / workflow
- review / PR comments
- debugging / testing
- work orders

### Queries foco
- `q01`
- `q05`
- `q09`

### Controles
- `q07`
- `q10`

### Criterios de éxito
- `q01` mejora `top3_contains_good_candidate`
- `q05` mejora `top3_contains_good_candidate`
- `q09` mejora `top3_contains_good_candidate`
- `q07` no degrada
- `q10` no degrada
- no aparecen severe false positives nuevos en negativos conocidos

### Candidate minimal aliases for Ola 2
No aplicados aún. Solo prearmados:
- planning/workflow:
  - `planificar`, `planificación`, `workflow`, `workflows`, `coordinar`, `coordinación`, `agentes`, `agentic`, `multi-agent`, `orquestación`
- review/PR comments:
  - `comentarios`, `review comments`, `PR comments`, `resolver comentarios`, `feedback de PR`, `branch quality gate`
- debugging/testing:
  - `flaky`, `test failure`, `pytest`, `debug tests`, `falla de test`
- work orders:
  - `work order`, `orden de trabajo`, `WO`, `ejecución por fases`

## Qué no toqué todavía
- no modifiqué Trifecta
- no toqué el wrapper productivo
- no mejoré harness/parser
- no agregué aliases todavía
- no reescribí SKILL.md todavía
- no ejecuté rerun de E1 ni E2 todavía
- no toqué producción

## Archivos producidos en esta fase
- `docs/reports/skill_hub_benchmark_manifest_reconciliation.md`
- `docs/reports/skill_hub_phase65_metadoc_hygiene.md`
- `docs/reports/skill_hub_phase65_canonicalization_minimal.md`
- `docs/reports/skill_hub_phase65_curation_plan.md`

## Estado general de Fase 6.5
**pass with issues**

Razón:
- la reconciliación y el diseño por olas quedaron claros
- aún no apliqué cambios concretos sobre el segmento porque el benchmark primero debía reconciliarse explícitamente y porque la causalidad de Ola 1 debe mantenerse limpia
