# Postmortem de recuperación — `skill-hub` después de Fase 6

## Resumen
El piloto Fase 6 no falló por comparabilidad ni por el harness.
Falló porque el corpus indexado y su metadata visible no ayudan a Trifecta a recuperar bien los slices `hard-positive` y `ambiguous`.

La evidencia apunta a un problema de **curación del corpus y metadata buscable**, no a falta de backbone en Trifecta.

Conclusión corta:
- `skill-hub` **sí tiene arreglo por curación del corpus**.
- El caso de uso **no está mal planteado**.
- Pero hoy el segmento mezcla demasiado:
  - documentos del hub sobre sí mismo
  - prefijos/source labels ruidosos
  - duplicados cross-source sin canonización visible
  - alias casi nulos para planning/review/workflow/agentic intent
  - algunos nombres/targets esperados que ni siquiera existen con ese nombre en el índice real

## Ranking de causas raíz
### 1. Contaminación del corpus con documentos del hub y metadocs no-skill
Evidencia:
- `q02` devolvió `prime_skills-hub` y `agent_skills-hub` como top hits.
- `q12` devolvió `AGENTS.md` como segundo resultado.
- `context_pack.json` incluye `prime_skills-hub.md`, `agent_skills-hub.md`, `session_skills-hub.md`, `AGENTS.md`, `README.md` como source files indexables.

Impacto:
- queries abstractas o de workflow son absorbidas por documentos de inventario/configuración del hub, no por skills operativas.

### 2. Alias coverage extremadamente pobre para planning / workflow / review / agentic
Evidencia:
- `aliases.yaml` solo tiene expansión fuerte para writing/editing, en inglés y español.
- No hay cobertura visible para:
  - planificar
  - workflow / workflows
  - agentes / agentic / multi-agent
  - branch review / PR comments
  - work order / orchestration

Impacto:
- las queries difíciles no reciben expansión útil hacia el vocabulario real de los skills correctos.

### 3. Naming drift y prefijos ruidosos dominan ranking
Evidencia:
- hits top incluyen `examen-*`, `superpowers-*`, `plugin-*`, `official-*`, `adr-*`, incluso cuando hay skills canónicos más útiles.
- `q05` top1=`plugin-metodo-tdd-first-python`, top2=`superpowers-systematic-debugging`, mientras `debug-helper` aparece recién 4º.
- `q09` top1=`branch-review`, no `branch-review-api` ni `learned-pr-feedback-resolution`.

Impacto:
- el ranking favorece artefactos con naming/token match accidental o prefijos de source, en vez de skills canónicos.

### 4. Mismatch entre benchmark/corpus subset y el índice real
Evidencia directa contra el manifest congelado:
- `methodology-workflows`: no existe con ese nombre
- `work-order-workflows`: no existe con ese nombre
- `systematic-debugging`: no existe con ese nombre exacto
- `root-cause-tracing`: no existe con ese nombre exacto
- `examen-code-review-checklist`: no existe con ese nombre exacto

Impacto:
- parte del benchmark espera nombres canónicos o subset labels que el índice real no expone con ese surface form.
- esto no invalida el piloto, pero sí revela un gap de curación/canonización del corpus real.

### 5. Descripciones buscables insuficientes o demasiado específicas en skills correctos
Evidencia:
- `branch-review-api` está muy centrado en `reviewctl`/`branch reviews`, menos en "resolver comentarios de review en una PR".
- `debug-helper` dice "error analysis, log interpretation, performance profiling"; no empuja fuerte términos como `flaky tests`, `pytest`, `test failure`.
- `tmux-plan-auditor` sí habla de revisión de planes, pero faltan vecinos semánticos para `planificar trabajo con agentes`, `coordinación`, `orquestación`, `multi-agent workflow` a nivel de alias/metadata superficial.

Impacto:
- aunque el skill correcto exista, el vocabulario visible no compite bien contra ruido o duplicados.

---

## Tabla fail -> causa probable -> evidencia

| Query | Qué debió aparecer | Qué apareció | Causa probable | Evidencia |
|---|---|---|---|---|
| `q01` `optmizar procesos agenticos` | `tmux-plan-auditor`, `workorder-execution-base`, `strategic-compact`, `verification-loop` | A: `examen-pm2-monitor`; B: `examen-dispatching-parallel-agents`, `superpowers-dispatching-parallel-agents`, `prime_skills-hub` | alias ausente para agentic/planning + ruido de prefijos + query abstracta contra corpus pobremente curado | raw A/B muestran pm2/dispatching/meta docs; aliases no cubre agentes/orquestación; `ctx get` debilitó top1 B |
| `q02` `quiero una skill para planificar trabajo con agentes` | `tmux-plan-auditor`, `workorder-execution-base`, `strategic-compact`, `verification-loop` | A/B: `prime_skills-hub`, `agent_skills-hub`, `official-figma-code-connect-components` | contaminación del corpus por docs del hub + ausencia de alias planning/agentes | raw A/B q02; `context_pack.json` incluye `prime_skills-hub.md` y `agent_skills-hub.md` |
| `q05` `debug flaky tests in python` | `debug-helper`, `python-testing`, `tdd-workflow`; adyacente: `systematic-debugging` | A/B top3: `plugin-metodo-tdd-first-python`, `superpowers-systematic-debugging`, `plugin-metodo-fp-python-backend` | naming/source-label drift + descripciones del skill correcto poco competitivas + adyacente no canonizado | `debug-helper` existe pero quedó 4º; `systematic-debugging` no existe como nombre exacto en manifest, solo variante `superpowers-*` |
| `q09` `quiero resolver comentarios de review en una PR` | `branch-review-api`, `github-pr-curated`, `learned-pr-feedback-resolution`; adyacente `verification-loop` | A/B: `branch-review`, `security-review`, `examen-requesting-code-review` | alias español ausente para PR comments + duplicate/source noise + wording del skill correcto demasiado específico | `learned-pr-feedback-resolution` existe en manifest pero no entra top3; aliases no cubre comentarios/review/PR |
| `q12` `how to coordinate multiple agents for a development task` | `tmux-plan-auditor`, `strategic-compact`, `workorder-execution-base`, `verification-loop` | A/B: `adr-agents-plugin`, `AGENTS.md`, `examen-fork-branch-workflow` | corpus contaminado por docs/ADR + falta de naming visible para coordination/orchestration + query abstracta | raw q12 devuelve `ADR agents`, `AGENTS.md`, `fork-branch-workflow`; nada de canon workflows |

---

## Aislamiento detallado de los fails

### q01 — typo + intent abstracto agentic
- Debieron aparecer: `tmux-plan-auditor`, `workorder-execution-base`, `strategic-compact`, `verification-loop`
- Apareció:
  - A: `examen-pm2-monitor`
  - B: `examen-dispatching-parallel-agents`, `superpowers-dispatching-parallel-agents`, `prime_skills-hub`
- Diagnóstico:
  - `aliases.yaml` no cubre `agenticos`, `agentes`, `orquestación`, `workflow`, `planificación`
  - el corpus premia skills con tokens superficiales como `agents`
  - `ctx get` mostró que `dispatching-parallel-agents` era sobre tareas independientes, no planificación/orquestación
- Causa dominante: aliases + naming visible + ruido cross-source

### q02 — planificación con agentes
- Debieron aparecer: `tmux-plan-auditor`, `workorder-execution-base`, `strategic-compact`, `verification-loop`
- Apareció:
  - `prime_skills-hub`
  - `agent_skills-hub`
  - `official-figma-code-connect-components`
- Diagnóstico:
  - query abstracta + corpus contaminado por documentos del propio hub
  - la palabra `skill` hace que el sistema recupere docs sobre el índice de skills
- Causa dominante: corpus contamination por metadocs indexados

### q05 — flaky tests en Python
- Debieron aparecer: `debug-helper`, `python-testing`, `tdd-workflow`
- Podía aparecer como adyacente: variante canónica de `systematic-debugging`
- Apareció:
  - `plugin-metodo-tdd-first-python`
  - `superpowers-systematic-debugging`
  - `plugin-metodo-fp-python-backend`
- Diagnóstico:
  - el skill correcto (`debug-helper`) existe pero queda detrás de prefijos plugin/superpowers
  - `systematic-debugging` existe semánticamente, pero el nombre visible real está prefijado
  - `debug-helper` no enfatiza `test failure`, `flaky`, `pytest`
- Causa dominante: naming drift + descripción buscable insuficiente

### q09 — resolver comentarios de review en una PR
- Debieron aparecer: `branch-review-api`, `github-pr-curated`, `learned-pr-feedback-resolution`
- Apareció:
  - `branch-review`
  - `security-review`
  - `examen-requesting-code-review`
- Diagnóstico:
  - `learned-pr-feedback-resolution` existe, pero no gana vocabulario español (`comentarios`, `review`, `PR`)
  - `branch-review-api` está sesgado a reviewctl/branch gate, no a comment resolution
  - alias español casi nulo para este dominio
- Causa dominante: aliases + contenido buscable de SKILL.md

### q12 — coordinar múltiples agentes
- Debieron aparecer: `tmux-plan-auditor`, `strategic-compact`, `workorder-execution-base`, `verification-loop`
- Apareció:
  - `adr-agents-plugin`
  - `AGENTS.md`
  - `examen-fork-branch-workflow`
- Diagnóstico:
  - la palabra `agents` arrastra documentos administrativos y plugin ADR
  - no hay canon workflow/orchestration suficientemente visible para competir
- Causa dominante: corpus contamination + naming visible insuficiente en skills correctos

---

## Cambios mínimos permitidos al corpus / metadata

### C1. Sacar del espacio de búsqueda principal los metadocs del hub que no son skills ejecutables
Aplicar a:
- `prime_skills-hub.md`
- `agent_skills-hub.md`
- `session_skills-hub.md`
- `AGENTS.md`
- `README.md`

No es cambio de Trifecta.
Es curación del segmento/corpus para que `skill-hub` no compita contra su propia documentación.

### C2. Canonizar naming visible en el corpus indexado
Objetivo:
- que el nombre visible principal sea el skill canónico, no el prefijo de source

Ejemplos:
- exponer `systematic-debugging` además de `superpowers-systematic-debugging`
- exponer `code-review-checklist` además de `examen-*` si aplica
- evitar que `examen-*`, `plugin-*`, `official-*`, `adr-*` dominen el surface form cuando el skill real tiene un nombre canónico reutilizable

### C3. Curar duplicados cross-source
Regla mínima:
- si hay skill duplicado con mismo contenido o mismo nombre funcional, mantener una entrada canónica visible y dejar duplicados como secundarios/no preferidos en el corpus indexable

Casos evidentes:
- `dispatching-parallel-agents`
- `python-testing`
- `tdd-workflow`
- `strategic-compact`
- `learned-pr-feedback-resolution`

### C4. Expandir aliases solo en dominios faltantes
Agregar aliases mínimos para:
- planning/workflow:
  - `planificar`, `planificación`, `orquestación`, `workflow`, `workflows`, `coordinación`, `coordinar`, `multi-agent`, `agentes`, `agentic`
- review/PR:
  - `comentarios`, `review comments`, `PR comments`, `feedback de PR`, `resolver comentarios`, `branch quality gate`
- debugging/testing:
  - `flaky`, `test failure`, `pytest`, `falla de test`, `debug tests`
- work orders:
  - `work order`, `orden de trabajo`, `WO`, `ejecución por fases`

### C5. Mejorar contenido buscable de SKILL.md en skills correctos
Sin cambiar arquitectura, solo ampliar superficie semántica visible.

Skills a reforzar:
- `tmux-plan-auditor`
  - agregar vocabulario: planificación, plan técnico, multi-agent, coordinación, orquestación
- `workorder-execution-base`
  - agregar vocabulario: work order workflow, phased execution, agent coordination
- `debug-helper`
  - agregar: flaky tests, test failures, pytest debugging
- `branch-review-api`
  - agregar: PR comments, review feedback, branch quality gate, resolve review comments
- `learned-pr-feedback-resolution`
  - agregar frases en español: resolver comentarios de review, feedback en PR, comentarios de CodeRabbit/Copilot
- `verification-loop`
  - agregar visibilidad como quality gate / branch gate / pre-merge verification

### C6. Corregir mismatch entre subset/benchmark y el índice real
No cambiar Trifecta; sí curar consistencia del corpus:
- alinear nombres esperados con nombres reales indexados, o
- introducir aliases/nombres visibles canónicos para los skills esperados

Casos concretos:
- `methodology-workflows`
- `work-order-workflows`
- `systematic-debugging`
- `root-cause-tracing`
- `examen-code-review-checklist`

Si esos nombres son parte del modelo mental deseado, deben existir como nombres visibles o aliases reales en el segmento.

---

## Experimento siguiente, pequeño y compatible con Trifecta
Propuesta mínima de siguiente experimento:

### E1 — Curación de corpus y metadata, sin tocar engine
Hacer solo este paquete chico:
1. excluir metadocs no-skill del espacio principal de búsqueda
2. agregar aliases workflow/review/debugging mínimos
3. canonizar 5–10 nombres visibles de skills de alto valor
4. reforzar 5 SKILL.md con vocabulario buscable faltante
5. reducir duplicados más ruidosos en el segmento indexado

### E2 — Re-run pequeño, no todo el piloto
Repetir solo estas queries primero:
- `q01`
- `q02`
- `q05`
- `q09`
- `q12`
- y controles `q07`, `q10`

Criterio de éxito del mini re-run:
- al menos `top3_contains_good_candidate=true` en los 5 fails actuales
- sin degradar `q07` ni `q10`
- sin introducir severe false positives en negativos ya conocidos

Eso sigue siendo 100% compatible con Trifecta y evita expansión innecesaria.

---

## Veredicto final
**`skill-hub` sí tiene arreglo por curación del corpus/metadata.**

No veo evidencia de que el caso de uso esté mal planteado.
Lo que está mal hoy es la calidad del segmento como superficie de búsqueda:
- demasiado metadoc indexado
- naming canónico inconsistente
- aliases casi vacíos fuera de writing
- duplicados/source labels ruidosos
- descriptions insuficientes en algunos skills correctos

En otras palabras:
- el problema principal **no** es Trifecta
- el problema principal **no** es falta de “inteligencia” del harness
- el problema principal es que el corpus actual no está curado para este caso de uso

Si se corrige esa curación, `skill-hub` puede seguir siendo un adaptador simple sobre Trifecta sin necesidad de sistema paralelo.
