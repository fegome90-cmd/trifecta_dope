**Metrics:**
- `symbol_resolve_success_rate`: % queries resolved
- `skeleton_cache_hit_rate`: Cache efficiency
- `bytes_read_per_task`: Total bytes loaded per symbol query
- `symbol_disambiguation_rate`: % queries requiring user disambiguation

**Rollback Plan:**
- If disambiguation >30% (ambiguous results): Make symbol queries explicit (`--kind function|class|module`)
- If bytes_read_per_task >10KB average: Reduce skeleton details further
- If disclosure inference too noisy: Fall back to explicit CLI param (`--disclosure skeleton|excerpt|raw`)

---
