### BLOCKER #5: Dataset Generator No Existe
**Causa**: `scripts/generate_benchmark_dataset.py` mencionado pero no implementado  
**Evidencia**: AUDIT:L363-L373  
**Fix mínimo**: Crear script que genere 10K events sintéticos  
**Test/Gate**: `wc -l /tmp/bench.jsonl` → 10000

---
