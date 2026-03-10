# Review B — Calidad del benchmark (adversarial)

## Hallazgos
### B1 — El dataset puede estar parcialmente sobreajustado a la hipótesis del plan
La muestra fue diseñada a partir de findings ya observados: typo abstracto, español, workflow, review, security, TDD. Eso tiene valor de piloto, pero también sesga el experimento hacia los lugares donde Variant B debería lucir mejor.

No veo queries hostiles suficientes contra la propia estrategia propuesta, por ejemplo:
- queries largas ya “instruction-shaped” donde rewrite podría meter ruido
- queries con intención mixta pero resoluble sin fallback
- queries donde alias expansion podría sobrecorregir

### B2 — Los negativos existen, pero todavía son pocos y relativamente nobles
Solo hay dos negativos explícitos (`q13`, `q14`). Para un piloto de coherencia quizá alcanza, pero para una review adversarial no es suficiente.

Problema:
- ambos negativos ya están conceptualizados como ambigüedad/sobreconfianza
- falta un negativo duro donde el sistema tenga alta tentación de elegir un skill popular pero incorrecto
- falta un negativo bilingüe con tokens muy cercanos a skills legítimas

### B3 — El corpus subset puede sesgar demasiado el resultado
El subset fue curado con intención explicable, pero eso también reduce el espacio de error. Un retrieval policy suele verse mejor en un universo pequeño y semisaneado.

Además:
- algunos duplicados se retienen a propósito
- otros posibles competidores ruidosos quedan fuera
- el choice de duplicados retained/excluded puede favorecer ciertos dominios

Sin un criterio más duro de representatividad, el benchmark corre riesgo de demostrar robustez en un entorno más limpio que el real.

### B4 — Thresholds son razonables para piloto, pero indulgentes para 14 queries
Con 14 queries:
- `top1_useful >= 0.50` equivale a ~7/14
- `top3_contains_good_candidate >= 0.83` equivale a ~12/14
- `severe_false_positives <= 1`

Lectura adversarial:
- 50% top1 útil es una vara baja si el objetivo es recomendar skills, no solo explorar retrieval
- permitir 1 severe false positive sobre 14 puede ser demasiado permisivo si ocurre en un hard-positive o en un negativo con alta confianza

### B5 — Difficulty y control_type no están todavía conectados a thresholds diferenciados
El dataset etiqueta `difficulty` y `control_type`, pero el plan no aplica thresholds ni análisis estratificado por esos campos.

Resultado:
- una mejora global puede esconder fracaso en hard-positives
- un buen promedio puede convivir con mal comportamiento en queries hostiles, que son precisamente las que justifican el piloto

## Debilidades
- pocos negativos realmente hostiles
- subset posiblemente demasiado favorable al piloto
- thresholds globales indulgentes para muestra chica
- sin lectura estratificada por dificultad/control

## Riesgo priorizado
**Riesgo B-P1 — Benchmark complaciente**

El piloto podría “ganar” porque el dataset y el subset están calibrados hacia la hipótesis Variant B y porque los thresholds permiten resultados mediocres parecer aceptables.

## Decisión
**FAIL**
