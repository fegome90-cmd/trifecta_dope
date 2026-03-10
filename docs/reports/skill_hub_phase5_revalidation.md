# Fase 5 — Nueva validación

## Qué validé
Artefactos revalidados:
- `.pi/plan/skill-hub-cloop-master.md`
- `.pi/plan/skill-hub-trifecta-alignment-sample-first.md`
- `docs/reports/skill_hub_variant_b_spec.md`
- `docs/reports/skill_hub_ab_output_schema.md`
- `data/skill_hub_pilot_queries.yaml`
- `docs/reports/skill_hub_independent_reviewer_protocol.md`

Modo:
- revalidación adversarial de consistencia interna
- operabilidad de reglas
- jerarquía de decisión
- cierre de ambigüedades metodológicas
- sin ejecutar benchmark
- sin tocar producción

## V1 — Consistencia cruzada
### Validado
- dataset size: consistente en `16`
- slices requeridos: `hard-positive`, `ambiguous`, `negative`
- subset application mode: consistente en plan + spec
- fail-close rules: presentes en master + sample-first + schema + protocol
- no-regression controls: `q04`, `q07`, `q10` consistentes
- negative overclaim rules: consistentes entre dataset, spec, schema y protocol
- confidence handling: consistente en líneas generales
- invalid run criteria: presentes y verificables en protocol; consistentes con schema/plan

### Contradicciones encontradas
- No encontré contradicciones materiales después del parche de jerarquía.

### Ambigüedades abiertas
- `acceptable_adjacent_skills` sigue siendo una válvula controlada que requiere disciplina del reviewer, pero ya no rompe consistencia.

### Regla aclarada
- Se congeló la jerarquía de decisión en plan maestro, sample-first y reviewer protocol.

### Veredicto V1
**PASS**

## V2 — Operabilidad de reglas
### Validado
- `acceptable_adjacent_skills`: operable si se usa solo para `top1_useful`/`top3_contains_good_candidate`, no para rescatar negativos ni romper no-regression
- `invalid run`: operable y auditable porque depende de evidencia concreta faltante o drift verificable
- blind vs semi-blind fallback: operable; el fallback queda permitido solo con justificación explícita
- `ctx get` contradiction rule: operable porque fuerza dos salidas observables (`confidence=low` o cambio de recomendación)
- separación retrieval / confidence / presentation: operable porque schema exige raw output path, presentation path y `confidence_reason_codes`

### Contradicciones encontradas
- Ninguna material.

### Ambigüedades abiertas
- La separación retrieval/confidence/presentation es auditable, pero la calidad real del parser solo podrá probarse en Fase 6.
- `acceptable_adjacent_skills` no tiene taxonomía formal; depende del dataset congelado y del protocolo.

### Regla aclarada
- En el protocolo quedó explícito que `acceptable_adjacent_skills` no rescata negativos ni no-regression.
- `no sufficient evidence` quedó con lectura operativa, no solo narrativa.

### Veredicto V2
**PASS WITH ISSUES**

## V3 — Jerarquía de decisión
### Jerarquía congelada
1. `invalid run`
2. `no_regression_positive_controls` failure
3. severe false positive en negativos, incluyendo `medium-confidence overclaim` sin evidencia suficiente
4. failure en slices críticos (`hard-positive`, `ambiguous`, `negative`)
5. thresholds globales

### Validación
- Ya no queda implícita; está escrita en:
  - `.pi/plan/skill-hub-cloop-master.md`
  - `.pi/plan/skill-hub-trifecta-alignment-sample-first.md`
  - `docs/reports/skill_hub_independent_reviewer_protocol.md`
- También quedó congelado que un éxito de nivel inferior no puede sobreescribir un fallo de nivel superior.

### Contradicciones encontradas
- Ninguna material.

### Ambigüedades abiertas
- `pass with issues` sigue dependiendo de que los issues no activen items 1-4. Eso ya está suficientemente acotado.

### Regla aclarada
- `pass with issues` solo aplica si no fallan items 1-4.
- `fail` es obligatorio si falla cualquier item 2-4 aunque pasen thresholds globales.

### Veredicto V3
**PASS**

## V4 — Ambigüedades residuales
### Hallazgos
#### A1 — `acceptable_adjacent_skills` sigue siendo el principal escape hatch residual
Está mucho mejor contenido, pero sigue dependiendo de curación humana del dataset y del criterio del reviewer para casos no listados.

#### A2 — `confidence` sigue siendo una política discreta con fricción real en casos frontera
Aunque la rúbrica está bastante cerrada, todavía puede haber casos donde `medium` y `low` compitan en queries ambiguas con top3 razonable pero evidencia conflictiva.

#### A3 — `negative` vs `ambiguous` está razonablemente separado, pero sigue siendo sensible a etiquetado de dataset
No veo contradicción, pero sí una dependencia fuerte de que las etiquetas congeladas no se muevan sin version bump.

#### A4 — `pass with issues` ya no es escape hatch fuerte
Después del parche, no sirve para tapar fallas reales de validez. Queda como estado menor y aceptable.

### Contradicciones encontradas
- Ninguna material.

### Qué sigue abierto
- ambigüedad residual controlada en:
  - frontera `medium` vs `low`
  - adyacentes no listados pero razonables

### Regla aclarada
- El protocolo ahora define `no sufficient evidence` de forma operativa y acota `acceptable_adjacent_skills`.

### Veredicto V4
**PASS WITH ISSUES**

## V5 — Go / no-go para piloto evaluable
### Evaluación contra criterio de entrada
Solo podía ser `pass` si:
- no había contradicciones materiales
- las reglas eran operables
- la jerarquía quedaba explícita
- el reviewer protocol podía invalidar una corrida de forma verificable

Resultado:
- contradicciones materiales: no
- operabilidad: sí, con residuales menores
- jerarquía explícita: sí
- invalidación verificable: sí

### Veredicto V5
**PASS**

## Veredicto global
**PASS WITH ISSUES**

Razón:
- El plan parchado ya es internamente consistente, suficientemente fail-close y operable para entrar a Fase 6.
- Persisten ambigüedades menores, pero ya no son bloqueantes ni permiten invalidar el diseño metodológico por sí solas.
- No encontré contradicciones materiales que obliguen a volver a Fase 4.

## Issues residuales no bloqueantes
1. `acceptable_adjacent_skills` sigue requiriendo disciplina del reviewer
2. la frontera `medium` vs `low` en casos ambiguos solo se terminará de tensar con outputs reales
3. la separación retrieval/confidence/presentation está bien especificada, pero su cumplimiento práctico depende de la implementación del harness y parser en Fase 6

## Fase 6 prearmada — Piloto evaluable
No ejecutada todavía.

### Entrada mínima congelada
- plan maestro: `.pi/plan/skill-hub-cloop-master.md`
- plan sample-first: `.pi/plan/skill-hub-trifecta-alignment-sample-first.md`
- spec B: `docs/reports/skill_hub_variant_b_spec.md`
- schema A/B: `docs/reports/skill_hub_ab_output_schema.md`
- dataset: `data/skill_hub_pilot_queries.yaml`
- reviewer protocol: `docs/reports/skill_hub_independent_reviewer_protocol.md`

### Checklist de arranque para Fase 6
1. congelar hashes efectivos de dataset, subset, manifest, context pack, aliases, wrapper y parser
2. capturar baseline A con evidencia cruda por capa
3. construir harness B aislado sin tocar wrapper productivo
4. asegurar que B emita `confidence_reason_codes`
5. verificar abort fail-close antes de correr B
6. ejecutar A/B solo después de pasar ese preflight

### Condición de disciplina
- si alguna evidencia requerida falta, la corrida no entra a evaluación: `invalid run`
