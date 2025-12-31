## 7. Evaluacion y Bench

Directorio: `minirag-eval/`

Estructura:
- `minirag-eval/queries/` sets de queries
- `minirag-eval/specs/` criterios de evaluacion
- `minirag-eval/results/` resultados (no se versionan)
- `minirag-eval/run_bench.sh` runner
- `minirag-eval/summarize_results.py` resumen

Ejemplo:

```bash
bash minirag-eval/run_bench.sh lsp_ast_positive
python minirag-eval/summarize_results.py
```
