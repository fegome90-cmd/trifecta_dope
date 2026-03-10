# Review C — Riesgos y comparabilidad (adversarial)

## Hallazgos
### C1 — A y B todavía no son plenamente comparables si el baseline A sigue pasando por output presentation distinta
El schema A/B unifica campos, pero baseline A hoy nace de un wrapper + info card con presentación retrieval-centric. Variant B tendrá consolidación decision-centric.

Riesgo:
- gran parte de la “mejora” puede venir del parser o de la capa de consolidación
- no del retrieval policy en sí

Sin registrar output crudo y reglas de extracción equivalentes, la comparación puede ser parcialmente un benchmark de post-processing.

### C2 — Freeze documentado no equivale a freeze controlado
Se congelan hashes, pero el plan no obliga a abortar si cambian antes de A o antes de B. Tampoco exige evidencia de:
- wrapper baseline exacto
- comando exacto
- parser exacto
- orden de corrida

Adversarialmente, esto deja demasiada superficie para drift silencioso.

### C3 — Un reviewer independiente todavía no podría juzgar sin sesgo suficiente
Aunque hay schema y métricas, faltan reglas para blind review real:
- no está definido si el reviewer verá qué arm es A o B
- no hay guía de adjudicación para skills adyacentes/duplicados
- no hay protocolo para resolver conflictos entre `recommended_skill` y señales de top3

Eso hace que la evaluación dependa demasiado de contexto previo y de simpatía por la hipótesis Variant B.

### C4 — El criterio de severe false positive es demasiado suave en negativos
El dataset ya marca severe false positives, pero para una revisión dura en negativos (`q13`, `q14`) el estándar debería ser más estricto:
- no solo castigar cuando hay high-confidence wrong winner
- también castigar medium-confidence overclaim cuando la query es estructuralmente ambigua/contaminada

Si no, el sistema puede seguir fallando con aparente prudencia verbal mientras igual induce selección incorrecta.

### C5 — El benchmark puede quedar invalidado aunque mejore métricas
Casos invalidantes que hoy no están explícitos:
- Variant B mejora top1/top3 usando filtrado efectivo por subset o manifest, no por mejor retrieval policy
- mejora vía rewrite agresivo que solo funciona en estas 14 queries
- confianza “mejora” porque se vuelve conservadora en casi todo, degradando utilidad práctica
- baseline A queda peor representado por parser más pobre que el de B

## Debilidades
- comparabilidad contaminada por presentation/post-processing
- freeze sin fail-close
- independencia del reviewer insuficientemente blindada
- criterio suave para false positives en negativos

## Riesgo priorizado
**Riesgo C-P1 — Mejora no válida experimentalmente**

El piloto podría mostrar mejores métricas sin demostrar una mejora real del uso de Trifecta. Eso invalidaría cualquier decisión de pasar a implementación real.

## Decisión
**FAIL**
