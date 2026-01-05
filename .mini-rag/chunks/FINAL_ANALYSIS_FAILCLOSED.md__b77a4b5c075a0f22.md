### BLOCKER #3: Benchmark Determinista
**Causa**: Propuesta usa `time | grep` (no parseable, no determinista)  
**Evidencia**: AUDIT:L236-L250  
**Fix mínimo**: Script Python con `np.percentile()` → output JSON  
**Test/Gate**: `scripts/bench_session_query.py` → p95 < 100ms

---
