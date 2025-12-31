### Per-Feature Metrics (T9.3.4)

| Feature | TP | FP | FN | Precision | Recall | F1 |
|---------|----|----|----|-----------|--------|-----|
| fallback | 6 | 0 | 3 | 1.00 | 0.67 | 0.80 |
| observability_telemetry | 6 | 6 | 1 | 0.50 | 0.86 | 0.63 |
| context_pack | 5 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| token_estimation | 2 | 0 | 1 | 1.00 | 0.67 | 0.80 |
| arch_overview | 2 | 1 | 0 | 0.67 | 1.00 | 0.80 |
| prime_indexing | 2 | 0 | 1 | 1.00 | 0.67 | 0.80 |
| cli_commands | 2 | 2 | 0 | 0.50 | 1.00 | 0.67 |
| telemetry_flush | 1 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| code_navigation | 1 | 0 | 1 | 1.00 | 0.50 | 0.67 |
| chunk_retrieval_flow | 1 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| directory_listing | 1 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| import_statements | 1 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| get_chunk_use_case | 1 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| symbol_surface | 0 | 0 | 2 | 0.00 | 0.00 | 0.00 |

**Key Improvement**: context_pack achieved perfect F1=1.00 (TP=3→5, FN=2→0, FP=0)
