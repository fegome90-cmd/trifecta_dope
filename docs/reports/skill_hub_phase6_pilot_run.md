# Fase 6 — Piloto evaluable `skill-hub`

## Resumen ejecutivo
Se ejecutó el piloto A/B con un harness mínimo sobre Trifecta, sin tocar producción y sin crear infraestructura nueva.

Resultado del run:
- **Preflight**: pass
- **Comparabilidad fail-close**: pass
- **Brazo A**: ejecutado
- **Brazo B**: ejecutado
- **Veredicto del piloto**: **fail**

Razón dominante del veredicto:
- falla por **slice failure** en `hard-positive` y `ambiguous`
- no hubo `invalid run`
- no hubo `no_regression_positive_controls failure`
- no hubo `severe false positive` en negativos para B

Run dir congelado:
- `eval/results/skill_hub_phase6/20260309T134513Z`

## Bloque 1 — Preflight
### 1. Qué hice
- verifiqué existencia de artefactos congelados
- congelé hashes efectivos de dataset, subset, manifest, context pack, aliases, wrapper y parser
- validé coherencia cruzada mínima:
  - dataset size = 16
  - slices requeridos presentes
  - subset application mode consistente
  - fail-close fields presentes en schema
  - no-regression controls presentes
  - reglas de negativos endurecidos presentes
  - jerarquía de decisión consistente
- validé operabilidad de campos obligatorios por corrida

### 2. Qué evidencia dejé
- `eval/results/skill_hub_phase6/20260309T134513Z/preflight.json`
- `eval/results/skill_hub_phase6/20260309T134513Z/freeze.json`

### 3. Qué guardrail validé
- fail-close habilitado antes de correr A/B
- subset application mode respetado en papel
- no se ejecutó nada antes de congelar inputs

### 4. Qué riesgo apareció
- ninguno bloqueante en preflight

### 5. Estado
- **pass**

## Freeze efectivo
- dataset_sha256: `5ae7f4fe7a7c3df3cc4ac85ded279b4021e5a4e1e06635bdc84565025aca4dce`
- corpus_subset_sha256: `1454245da4d49b33912193b4d0b8b0a2333716d7ea57b4a3eaac2321ec834465`
- manifest_sha256: `5c853b2492a57f2d6b417218bfbf637d35b049f75529afd331ea9aa5a2058f23`
- context_pack_sha256: `01d70e074914940375112b9de1321c994562d6aedfca4c5513661cd604928855`
- aliases_sha256: `b3216237f1a2ca959c23efb2508501edefc7db95470a95f8eee064475ad351b5`
- wrapper_sha256 (productivo, congelado): `fa78432753b0811b8e6e222167ad67ca58ca6775f321edde5fbc37d94e6f3a7b`
- baseline_presentation_sha256: `3c2da28be55485f44784bf76b4f33cdd6a5d126c0399749a8125e640340ada94`
- parser_sha256 (harness mínimo): `d1692435ca1f1e2fec407893a4b512efccb3216a70fb33e3fa609a8e6e77045f`

## Bloque 2 — Harness mínimo
### 1. Qué hice
Creé un runner mínimo:
- `eval/scripts/skill_hub_phase6_pilot.py`

Funciones del harness:
- congelar hashes
- correr A con el wrapper actual
- correr B con `ctx search` + `ctx get` según spec
- guardar stdout/stderr crudos
- serializar filas al schema A/B
- evaluar comparabilidad fail-close
- emitir resumen del run

### 2. Qué evidencia dejé
- script: `eval/scripts/skill_hub_phase6_pilot.py`
- resultados normalizados: `eval/results/skill_hub_phase6/20260309T134513Z/rows.jsonl`
- resumen: `eval/results/skill_hub_phase6/20260309T134513Z/summary.json`

### 3. Qué guardrail validé
- no hubo retrieval propio
- no hubo índice paralelo
- no hubo reranking dominante externo
- el subset no prefiltró retrieval real
- el parser solo extrajo/normalizó campos y registró evidencia

### 4. Qué riesgo apareció
- la señal de `ctx get` fue útil para bajar confidence, pero no alcanzó para rescatar slices críticos

### 5. Estado
- **pass with issues**

## Bloque 3 — Evidencia A
### 1. Qué hice
- ejecuté el baseline con el wrapper actual por cada query
- capturé:
  - comando real usado
  - output crudo de retrieval
  - output final del wrapper
- serialicé al schema sin inventar confidence ni recommendation semantics no presentes en el baseline

### 2. Qué evidencia dejé
- raw A: `eval/results/skill_hub_phase6/20260309T134513Z/raw/A/`
- filas A en: `eval/results/skill_hub_phase6/20260309T134513Z/rows.jsonl`

### 3. Qué guardrail validé
- wrapper productivo no modificado
- baseline corrido tal como existe hoy

### 4. Qué riesgo apareció
- baseline no tiene capa nativa de confidence; eso quedó registrado como limitación del run, no corregido desde afuera

### 5. Estado
- **pass**

### Lectura breve A
- top1_useful_rate: `0.1875`
- top3_contains_good_candidate_rate: `0.25`
- severe_false_positives: `8`
- hard-positive slice: `0.0` top3 good candidate rate
- ambiguous slice: `0.0` top3 good candidate rate
- negative slice: `0` severe false positives

Ejemplos A:
- `q07`: recupera `security-review` correctamente
- `q10`: recupera `workorder-execution-base` correctamente
- `q01`: cae en `examen-pm2-monitor` con falso positivo severo

## Bloque 4 — Evidencia B
### 1. Qué hice
Ejecuté una variante B aislada y mínima:
- rewrite a instrucción solo cuando disparaba la regla
- `ctx search` como backbone real
- `ctx get` sobre top-3 para validar/disciplinar confidence
- fallback controlado solo si la señal era débil
- consolidación final con `confidence_reason_codes`

### 2. Qué evidencia dejé
- raw B: `eval/results/skill_hub_phase6/20260309T134513Z/raw/B/`
- filas B en: `eval/results/skill_hub_phase6/20260309T134513Z/rows.jsonl`
- presentaciones B en JSON por query

### 3. Qué guardrail validé
- no hubo bypass de Trifecta
- no hubo prefilter por subset
- no hubo rerank dominante por aliases
- cuando `ctx get` debilitó top1, se bajó confidence a `low`

### 4. Qué riesgo apareció
- la disciplina del flujo Trifecta mejoró trazabilidad y confidence, pero no mejoró recall/coherencia en slices críticos

### 5. Estado
- **pass with issues**

### Lectura breve B
- top1_useful_rate: `0.1875`
- top3_contains_good_candidate_rate: `0.25`
- confidence_matches_reality_rate: `0.9375`
- severe_false_positives: `8`
- hard-positive slice: `0.0` top3 good candidate rate
- ambiguous slice: `0.0` top3 good candidate rate
- negative slice: `0` severe false positives

Ejemplos B:
- `q07`: `security-review`, confidence `high`
- `q10`: `work-order-workflows`, confidence `high`
- `q01`: rewrite cambió el top1 a `examen-dispatching-parallel-agents`, pero `ctx get` lo debilitó y confidence bajó a `low`
- `q13`–`q16`: negativos quedaron en `low`, evitando overclaim severo

## Bloque 5 — Comparativa A/B
### 1. Qué hice
- comparé A vs B sobre el mismo dataset y hashes congelados
- verifiqué no-regression controls
- leí slices críticos
- apliqué la jerarquía de decisión congelada

### 2. Qué evidencia dejé
- `eval/results/skill_hub_phase6/20260309T134513Z/summary.json`
- `eval/results/skill_hub_phase6/20260309T134513Z/rows.jsonl`

### 3. Qué guardrail validé
- hashes estables entre A y B
- evidencia cruda por capa disponible
- comparabilidad mantenida bajo el schema

### 4. Qué riesgo apareció
- B mejora disciplina y confidence, pero no el rendimiento en hard-positive/ambiguous

### 5. Estado
- **fail**

## No-regression check
Controles:
- `q04`: pass
  - A: top1=false, top3=true
  - B: top1=false, top3=true
- `q07`: pass
  - A: top1=true, top3=true
  - B: top1=true, top3=true
- `q10`: pass
  - A: top1=true, top3=true
  - B: top1=true, top3=true

Resultado:
- **no_regression_positive_controls: pass**

## Severe false positives check
### Negativos
Brazo B:
- `q13`: low confidence, no severe false positive
- `q14`: low confidence, no severe false positive
- `q15`: low confidence, no severe false positive
- `q16`: low confidence, no severe false positive

Resultado:
- **negative severe false positives: pass**

### Positivos / ambiguos
Persisten falsos positivos severos en hard-positive y ambiguous slices.
Eso domina el veredicto final por jerarquía.

## Confidence observations
- A no tiene confidence nativa; quedó registrada como ausente
- B sí tuvo confidence trazable y en general conservadora
- `confidence_matches_reality_rate` de B fue alta (`0.9375`) porque el harness bajó confidence cuando `ctx get` debilitó top1
- esa mejora de disciplina **no rescata** la corrida porque no mejora los slices críticos

## Veredicto del run
Jerarquía aplicada:
1. `invalid run` → no
2. `no_regression_positive_controls failure` → no
3. `severe false positive` en negativos → no
4. failure en slices críticos → **sí** (`hard-positive`, `ambiguous`)
5. thresholds globales → ya no rescatan

Veredicto:
- **fail**

Motivo exacto:
- `hard-positive` slice failure
- `ambiguous` slice failure

## Confirmaciones explícitas
Confirmo que durante esta Fase 6:
- **no modifiqué Trifecta**
- **no creé un sistema paralelo**
- **no usé RAG genérico**
- **no toqué producción**
- el backbone real del piloto fue Trifecta (`skill-hub`, `ctx search`, `ctx get`)

## Artefactos mínimos creados
- runner mínimo: `eval/scripts/skill_hub_phase6_pilot.py`
- resultados: `eval/results/skill_hub_phase6/20260309T134513Z/`
- reporte: `docs/reports/skill_hub_phase6_pilot_run.md`
