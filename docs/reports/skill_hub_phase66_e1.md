# Fase 6.6 — E1 mini experimento de Ola 1 para `skill-hub`

## Scope exacto
Queries ejecutadas:
- foco: `q02`, `q12`
- controles: `q07`, `q10`

Restricciones respetadas:
- no se modificó Trifecta
- no se creó sistema paralelo
- no se tocó producción
- no se tocaron aliases
- no se tocó `SKILL.md`
- se reutilizó el mismo harness mínimo validado en Fase 6: `eval/scripts/skill_hub_phase6_pilot.py`

## 1. Freeze efectivo
Run dir:
- `eval/results/skill_hub_phase66_e1/20260309T165536Z`

Freeze explícito:
- `dataset_version`: `post-ola1-reconciled`
- `dataset_sha256`: `6cb747d8e11220895414cdde8a4ace9979214970c1756d27d58b740138185bbc`
- `corpus_subset_sha256`: `1454245da4d49b33912193b4d0b8b0a2333716d7ea57b4a3eaac2321ec834465`
- `manifest_sha256`: `5c853b2492a57f2d6b417218bfbf637d35b049f75529afd331ea9aa5a2058f23`
- `context_pack_sha256`: `abfbfd439d8287abafe4144cf6dbc96c4eb56d497c93f962a341b098de5005ab`
- `aliases_sha256`: `b3216237f1a2ca959c23efb2508501edefc7db95470a95f8eee064475ad351b5`
- `wrapper_sha256`: `fa78432753b0811b8e6e222167ad67ca58ca6775f321edde5fbc37d94e6f3a7b`
- `parser_sha256`: `d1692435ca1f1e2fec407893a4b512efccb3216a70fb33e3fa609a8e6e77045f`

Preflight / abort rules verificadas:
- evidencia cruda presente para A y B por query
- sin cambios de freeze entre queries
- serialización al schema comparable completada
- no se abortó por `missing_raw_evidence`
- no se abortó por `hash_change_without_explicit_freeze`
- no se abortó por `schema_serialization_failure`

Archivos de freeze:
- `eval/results/skill_hub_phase66_e1/20260309T165536Z/freeze.json`
- `eval/results/skill_hub_phase66_e1/20260309T165536Z/preflight.json`

## 2. Evidencia por query

### q02
- Phase 6 B:
  - top3: `prime_skills-hub`, `agent_skills-hub`, `official-figma-code-connect-components`
  - `top3_contains_good_candidate=false`
  - `severe_false_positive=true`
- E1 B:
  - top1: `official-figma-code-connect-components`
  - top3: `official-figma-code-connect-components`, `content-engine`, `test-pr-dev-lima-connection`
  - `top3_contains_good_candidate=false`
  - `severe_false_positive=true`
  - confidence: `low`

Lectura:
- desaparece la contaminación por metadocs (`prime_skills-hub`, `agent_skills-hub`)
- no aparece ningún candidato bueno en top3
- no mejora la métrica objetivo

### q12
- Phase 6 B:
  - top3: `adr-agents-plugin`, `AGENTS`, `examen-fork-branch-workflow`
  - `top3_contains_good_candidate=false`
  - `severe_false_positive=true`
- E1 B:
  - top1: `adr-agents-plugin`
  - top3: `adr-agents-plugin`, `examen-fork-branch-workflow`, `dispatching-parallel-agents`
  - `top3_contains_good_candidate=false`
  - `severe_false_positive=true`
  - confidence: `low`

Lectura:
- desaparece la contaminación por `AGENTS`
- aparece `dispatching-parallel-agents` en top3
- aun así no entra ningún candidato considerado bueno/adyacente por el benchmark
- no mejora la métrica objetivo

### q07
- Phase 6 B:
  - top3: `security-review`, `iterative-security-review`, `find-skills`
  - `top3_contains_good_candidate=true`
  - `severe_false_positive=false`
- E1 B:
  - top3: `security-review`, `iterative-security-review`, `find-skills`
  - `top3_contains_good_candidate=true`
  - `severe_false_positive=false`
  - confidence: `high`

Lectura:
- sin degradación

### q10
- Phase 6 B:
  - top3: `work-order-workflows`, `workorder-execution-base`, `examen-fork-branch-workflow`
  - `top3_contains_good_candidate=true`
  - `severe_false_positive=false`
- E1 B:
  - top3: `work-order-workflows`, `workorder-execution-base`, `examen-fork-branch-workflow`
  - `top3_contains_good_candidate=true`
  - `severe_false_positive=false`
  - confidence: `medium`

Lectura:
- sin degradación

## 3. Comparación contra Fase 6
Baseline usado:
- `eval/results/skill_hub_phase6/20260309T134513Z/rows.jsonl`

### Resumen comparativo
| query | Phase 6 B top3 good | E1 B top3 good | cambio | severe FP nuevo |
|---|---:|---:|---|---|
| `q02` | false | false | no mejora | no |
| `q12` | false | false | no mejora | no |
| `q07` | true | true | no degrada | no |
| `q10` | true | true | no degrada | no |

Contamination drop confirmado:
- `q02`: salen `prime_skills-hub` y `agent_skills-hub`
- `q12`: sale `AGENTS`

Pero benchmark improvement no confirmado:
- `q02`: sigue fallando
- `q12`: sigue fallando

Archivo de comparación:
- `eval/results/skill_hub_phase66_e1/20260309T165536Z/comparison.json`

## 4. Lectura pedida
- `q02` mejoró o no: **no**
- `q12` mejoró o no: **no**
- `q07` degradó o no: **no**
- `q10` degradó o no: **no**

## 5. Veredicto E1
Criterio de éxito pedido:
- `q02` y `q12` deben mejorar `top3_contains_good_candidate`
- `q07` y `q10` no deben degradarse
- no deben aparecer severe false positives nuevos

Resultado:
- targets: **fallan**
- controles: **pasan**
- severe false positives nuevos: **no aparecen**

Veredicto:
- **fail**

## Evidencia principal
- freeze: `eval/results/skill_hub_phase66_e1/20260309T165536Z/freeze.json`
- preflight: `eval/results/skill_hub_phase66_e1/20260309T165536Z/preflight.json`
- rows: `eval/results/skill_hub_phase66_e1/20260309T165536Z/rows.jsonl`
- summary: `eval/results/skill_hub_phase66_e1/20260309T165536Z/summary.json`
- comparison: `eval/results/skill_hub_phase66_e1/20260309T165536Z/comparison.json`
- verdict: `eval/results/skill_hub_phase66_e1/20260309T165536Z/verdict.json`
