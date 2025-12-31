### Pendiente (Inmediato)
- ⏳ C) ctx.plan command - PRIME-only planning
  - Leer `_ctx/prime_*.md` para index.entrypoints y index.feature_map
  - Salida JSON con selected_feature, plan_hit, chunk_ids, paths, next_steps
- ⏳ D) Dataset de evaluación (20 tareas: 10 meta + 10 impl)
- ⏳ E) Baseline y evaluación

**Pack SHA**: `5e6ad2eb365aea98`
**Comandos útiles**:
  - `trifecta ctx stats -s . --window 30`
  - `python3 scripts/telemetry_diagnostic.py --segment .`
