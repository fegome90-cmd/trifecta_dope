### ✅ B) Implementar ctx.stats

**Status**: COMPLETADO

**Archivos creados/modificados**:
- `src/application/use_cases.py` - Agregado `StatsUseCase`
- `src/infrastructure/cli.py` - Agregado comando `ctx stats`

**Comando**:
```bash
trifecta ctx.stats --segment . --window 30
```

**Output**:
- Resumen general (total_searches, hits, zero_hits, hit_rate, avg_latency_ms)
- Top zero-hit queries (top 10)
- Breakdown por query_type (meta/impl/unknown)
- Breakdown por hit_target (skill/prime/session/agent/other)

---
