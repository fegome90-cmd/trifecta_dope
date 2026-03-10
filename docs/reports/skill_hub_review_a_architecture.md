# Review A — Coherencia arquitectónica

## 1. Qué revisó
- `.pi/plan/skill-hub-cloop-master.md`
- `.pi/plan/skill-hub-trifecta-alignment-sample-first.md`
- `docs/reports/skill_hub_variant_b_spec.md`
- `docs/reports/skill_hub_ab_output_schema.md`
- `data/skill_hub_pilot_queries.yaml`
- `data/skill_hub_pilot_corpus_subset.yaml`

Foco:
- consistencia con restricciones del checkpoint
- alineación con contrato Trifecta Search -> Get
- aislamiento del piloto
- reversibilidad y ausencia de cambios de producción

## 2. Qué encontró
### A-F1 — La dirección arquitectónica del piloto es correcta
El plan mantiene a `skill-hub` como cliente/adaptador de Trifecta, preserva `Search -> Get`, separa retrieval de presentation y prohíbe tocar producción antes del go final. Eso está alineado con el objetivo del piloto.

### A-F2 — Hay una incoherencia operativa entre “corpus subset” y “usar el segmento existente”
El plan congela un `corpus subset v1`, pero al mismo tiempo decide usar `~/.trifecta/segments/skills-hub` como base del piloto y no especifica cómo ese subset limita realmente la evaluación.

Sin una regla explícita, hay dos interpretaciones incompatibles:
- el piloto corre sobre el corpus real completo del segmento
- el piloto corre sobre un universo filtrado al subset curado

Eso es un problema arquitectónico porque cambia el significado del benchmark y del aislamiento del piloto.

### A-F3 — Falta canonización explícita de fuente/candidato para el piloto
El subset usa etiquetas de fuente como `trifecta-workflows`, `pi-agent-skills`, `codex-skills`, etc. Discovery ya registró drift entre fuentes documentadas y reales. El plan no define una capa de canonización mínima para:
- mapear nombres de fuente del subset a fuentes observables en resultados
- distinguir “skill canónica” vs “duplicado por source”

No hace falta rediseñar la arquitectura, pero sí fijar esta regla para que la validación no dependa de nombres inconsistentes.

## 3. Qué decisión toma
Decisión: **REVISE / no pasa todavía**.

La arquitectura base del piloto es buena, pero hay un bloqueo metodológico-arquitectónico: el plan no define cómo se aplica el subset curado si el retrieval usa el segmento existente. Eso debe quedar cerrado antes de implementación real del harness.

## 4. Qué artefacto deja
Este review deja:
- `docs/reports/skill_hub_review_a_architecture.md`

Parche chico recomendado al plan:
- agregar una cláusula explícita de “subset application mode” con una de estas opciones:
  1. `full-segment retrieval + subset-only evaluation lens`, o
  2. `subset-filtered candidate evaluation after search`, o
  3. `pilot-isolated artifact copy` si las dos anteriores no alcanzan.
- agregar una tabla mínima de canonización `source_label -> observed_source_label` para evaluación.

## 5. Qué riesgo sigue abierto
- que el piloto termine evaluando un universo distinto del que el plan dice congelar
- que duplicados/fuentes ruidosas sean interpretados como errores del retrieval cuando en realidad son errores de nomenclatura/evaluación

## 6. Si pasa o no pasa
**NO PASA**
