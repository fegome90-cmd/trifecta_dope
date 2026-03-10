# Review C — Riesgos y comparabilidad

## 1. Qué revisó
- `.pi/plan/skill-hub-cloop-master.md`
- `.pi/plan/skill-hub-trifecta-alignment-sample-first.md`
- `docs/reports/skill_hub_variant_b_spec.md`
- `docs/reports/skill_hub_ab_output_schema.md`
- `data/skill_hub_pilot_queries.yaml`
- `data/skill_hub_pilot_corpus_subset.yaml`

Foco:
- comparabilidad real entre A y B
- freeze efectivo de baseline
- riesgo de drift entre corridas
- riesgo de conclusiones inválidas por ambigüedad experimental

## 2. Qué encontró
### C-F1 — El schema congela hashes, pero no congela suficiente evidencia de ejecución
El schema exige `manifest_sha256`, `context_pack_sha256` y `aliases_sha256`, lo cual está bien. Pero no obliga a registrar además:
- comando exacto usado por el baseline A
- versión/path del wrapper baseline
- salida cruda del baseline antes del parser/consolidación
- timestamp/orden de corrida A y B

Sin eso, dos corridas con los mismos hashes podrían seguir siendo difíciles de auditar si cambia el wrapper, el info card o el parser local.

### C-F2 — La comparabilidad queda comprometida si no se cierra el “subset application mode”
Este finding hereda el problema arquitectónico: si A y B consultan el segmento completo, pero la evaluación habla de subset curado, la comparación puede mezclar:
- performance del retrieval real
- performance del filtro/evaluación posterior
- ruido de fuentes no incluidas explícitamente en el subset

Eso vuelve ambiguo el significado de una mejora o regresión.

### C-F3 — Falta una regla explícita de verificación pre/post-run del freeze
El plan dice “freeze and record”, pero no fuerza una validación operacional tipo:
- verificar hashes antes de correr A
- verificar hashes antes de correr B
- abortar si cambia cualquier hash

Registrar no alcanza; hay que fail-close si el freeze se rompe.

## 3. Qué decisión toma
Decisión: **REVISE / no pasa todavía**.

La comparabilidad aún no está suficientemente cerrada para producir evidencia confiable. No propongo rearmar el experimento; solo faltan guardrails chicos pero obligatorios.

## 4. Qué artefacto deja
Este review deja:
- `docs/reports/skill_hub_review_c_risks_comparability.md`

Parches chicos recomendados al plan/schema:
- agregar campos de evidencia de ejecución:
  - `runner_command`
  - `wrapper_path`
  - `wrapper_sha256` o versión equivalente
  - `raw_output_path`
  - `run_started_at`
- agregar gate `freeze_verification_required=true` con abort si cambian hashes
- explicitar el `subset application mode` para que A/B signifique lo mismo

## 5. Qué riesgo sigue abierto
- drift silencioso entre baseline y variant
- conclusiones no auditables si la evidencia cruda no se conserva
- mejora aparente causada por diferencias de universo evaluado, no por la política Variant B

## 6. Si pasa o no pasa
**NO PASA**
