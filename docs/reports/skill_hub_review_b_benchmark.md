# Review B — Calidad del benchmark

## 1. Qué revisó
- `data/skill_hub_pilot_queries.yaml`
- `data/skill_hub_pilot_corpus_subset.yaml`
- `.pi/plan/skill-hub-trifecta-alignment-sample-first.md`
- `docs/reports/skill_hub_variant_b_spec.md`
- `docs/reports/skill_hub_ab_output_schema.md`

Foco:
- cobertura del dataset
- calidad de controles positivos/negativos
- claridad de la rúbrica
- utilidad del benchmark para discriminar A vs B

## 2. Qué encontró
### B-F1 — El benchmark es pequeño pero bien orientado para piloto
Las 14 queries cubren exactamente los casos que justifican el piloto:
- typo + intent abstracto
- español natural
- inglés natural
- workflow difuso
- controles positivos
- controles negativos por trampa léxica y semántica

Eso es suficiente para un piloto sample-first y evita scope creep.

### B-F2 — La rúbrica principal está bien elegida
Las métricas `top1_useful`, `top3_contains_good_candidate`, `confidence_matches_reality` y `severe_false_positives` están alineadas con el problema real: coherencia y sobreconfianza, no solo recall superficial.

### B-F3 — Falta una regla explícita para equivalencias aceptables en skills “adyacentes”
Hoy la evaluación depende de `expected_good_skills` exactas por nombre. Eso funciona en muchos casos, pero puede penalizar resultados razonables cuando aparece:
- un skill canónico duplicado por otra fuente
- un skill adyacente correcto pero no listado
- un skill de workflow más general que cumple la intención

El problema no exige rehacer la rúbrica; alcanza con un parche chico de equivalencias permitidas o “acceptable adjacent skills” por query.

### B-F4 — Los controles negativos están bien planteados, pero requieren disciplina de scoring
`q13` y `q14` son útiles porque miden sobreconfianza, no ausencia total de resultados. Eso es correcto.

Riesgo: si el evaluador no sigue una guía consistente para `confidence_matches_reality`, esos casos pueden volverse subjetivos.

## 3. Qué decisión toma
Decisión: **PASS con findings menores**.

El benchmark sirve para la fase piloto y discrimina razonablemente entre baseline y Variant B. No veo un bloqueo que impida seguir a Fase 4, pero sí conviene endurecer dos reglas pequeñas antes de ejecutar el A/B real.

## 4. Qué artefacto deja
Este review deja:
- `docs/reports/skill_hub_review_b_benchmark.md`

Parches chicos recomendados al plan/dataset:
- agregar por query un campo opcional `acceptable_adjacent_skills`
- agregar una mini scoring note para negativos: cuándo `confidence_matches_reality` vale true en queries ambiguas/negativas

## 5. Qué riesgo sigue abierto
- subjetividad residual en scoring de confianza
- falsos negativos metodológicos si una respuesta útil cae fuera de `expected_good_skills` estrictas

## 6. Si pasa o no pasa
**PASA**
