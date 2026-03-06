# Checklist - Global Skills Pilot

**Checkpoint**: `20260305-global-skills-pilot`
**Plan fuente**: `.pi/plan/trifecta-global-skills-pilot.md`

## Tasks
- [ ] A1 Crear segmento `skills-hub`.
- [ ] A2 Definir `sources.yaml` + exclusiones.
- [ ] B1 Generar `skills_manifest.json`.
- [ ] C1 Ejecutar `ctx sync` exitoso.
- [ ] C2 Ejecutar query pack y guardar métricas.
- [ ] D1 Publicar guideline de uso + fallback.
- [ ] E1 Reporte final con `GO/NO-GO`.

## Instruction for next agent
1. Ejecutar solo piloto (`skills-hub`), no mezclar con implementación del plan global principal.
2. Respetar contrato de fallback:
   - `status=empty` o `status=error` => fallback local obligatorio.
3. Registrar métricas mínimas: `search_latency_ms` p50/p95, `top3_relevance_rate`, `coverage_rate`.
4. Entregar reporte final con recomendación explícita `GO` o `NO-GO`.
5. No tocar código productivo fuera del scope del piloto.
