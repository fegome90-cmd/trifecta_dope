# Review A — Coherencia arquitectónica (adversarial)

## Hallazgos
### A1 — El plan todavía parece adaptador sobre Trifecta, pero no lo demuestra operativamente
En papel, Variant B conserva `ctx search` y `ctx get`. Eso cumple el discurso de adaptador. Pero el plan no fija un test de arquitectura que falle si el harness:
- usa manifest para prefiltrar candidatos antes del retrieval real
- usa aliases como ranking paralelo en vez de soporte de reformulación
- decide el ganador principalmente por heurísticas fuera del engine

Conclusión adversarial: hoy la arquitectura declarada es correcta, pero todavía podría degenerar en un “pseudo-adaptador” donde Trifecta solo decora una decisión tomada afuera.

### A2 — `Search -> Get` puede quedar ornamental
El spec dice que `ctx get --mode excerpt` valida top candidatos. Pero no define un criterio de impacto obligatorio sobre la recomendación final.

Riesgo concreto:
- `search` produce un top1 dudoso
- `get` devuelve excerpt conflictivo
- el sistema igual mantiene ese top1 y solo baja confidence

Si eso ocurre, `Get` no está corrigiendo retrieval; solo agrega narrativa. En ese caso `Search -> Get` existe formalmente, pero no cambia la decisión.

### A3 — Manifest y aliases siguen siendo una vía potencial de bypass
El plan reconoce hashes de manifest/context/aliases y permite alias-aware fallback. Bien.

Problema adversarial:
- no hay límite explícito al peso que aliases puede tener en rewrite/fallback
- no hay prohibición explícita de usar manifest metadata para rerank fuerte o descarte previo

Eso abre una ruta de contaminación: la mejora del Variant B podría venir de metadatos auxiliares y no de un mejor uso de Trifecta retrieval.

### A4 — Separación retrieval / confidence / presentation es buena en el spec, floja en verificabilidad
El spec los separa conceptualmente, pero no fija evidencia auditable de esa separación.

Faltan artefactos/pistas para comprobar:
- qué parte fue salida pura de retrieval
- qué parte fue reinterpretación para confidence
- qué parte fue formatting/presentation

Sin esa trazabilidad, la separación puede romperse sin que el benchmark lo detecte.

## Debilidades
- Falta un guardrail anti-bypass explícito.
- Falta un criterio obligatorio de “excerpt conflict changes recommendation or forces low confidence”.
- Falta evidencia estructurada por etapa para verificar separación de políticas.

## Riesgo priorizado
**Riesgo A-P1 — Falso alineamiento arquitectónico**

El piloto podría parecer Trifecta-aligned, pero en realidad ganar por heurísticas externas apoyadas en manifest/aliases y por un `Get` sin efecto decisorio real. Si eso pasa, cualquier mejora del benchmark sería arquitectónicamente inválida.

## Decisión
**FAIL**
