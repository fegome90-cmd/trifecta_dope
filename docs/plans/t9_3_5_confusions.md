# T9.3.5 Confusion Report

**Generated**: 2025-12-31T18:39:34.493280

---

## Dataset Identity

- **Path**: `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/t9-3-5-audit-fix/docs/plans/t9_plan_eval_tasks_v2_nl.md`
- **SHA256**: `610e7bc4ebf14ad2`
- **mtime**: `2025-12-31T14:57:19.475178`

---

## Run Identity

- **Segment**: `.`
- **Commit**: `06393ba`
- **Timestamp**: `2025-12-31T18:39:34.493509`

---

## Per-Feature Metrics (TP/FP/FN)

| Feature | TP | FP | FN | Precision | Recall | F1 |
|---------|----|----|----|-----------|--------|----|
| arch_overview | 2 | 1 | 0 | 0.67 | 1.00 | 0.80 |
| chunk_retrieval_flow | 1 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| cli_commands | 2 | 3 | 0 | 0.40 | 1.00 | 0.57 |
| code_navigation | 1 | 0 | 1 | 1.00 | 0.50 | 0.67 |
| context_pack | 3 | 0 | 2 | 1.00 | 0.60 | 0.75 |
| directory_listing | 1 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| fallback | 6 | 3 | 3 | 0.67 | 0.67 | 0.67 |
| get_chunk_use_case | 1 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| import_statements | 1 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| observability_telemetry | 5 | 5 | 2 | 0.50 | 0.71 | 0.59 |
| prime_indexing | 2 | 0 | 1 | 1.00 | 0.67 | 0.80 |
| symbol_surface | 0 | 0 | 2 | 0.00 | 0.00 | 0.00 |
| telemetry_flush | 1 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| token_estimation | 2 | 0 | 1 | 1.00 | 0.67 | 0.80 |

---

## Top Confusions (Expected -> Got)

Top 10 confusion pairs by frequency:

| Rank | Expected | Got | Count | Example Task IDs |
|------|----------|-----|-------|-------------------|
| 1 | fallback | observability_telemetry | 2 | #4, #8 |
| 2 | symbol_surface | fallback | 2 | #17, #35 |
| 3 | code_navigation | observability_telemetry | 1 | #34 |
| 4 | context_pack | cli_commands | 1 | #24 |
| 5 | context_pack | observability_telemetry | 1 | #20 |
| 6 | fallback | cli_commands | 1 | #30 |
| 7 | observability_telemetry | cli_commands | 1 | #19 |
| 8 | observability_telemetry | fallback | 1 | #25 |
| 9 | prime_indexing | arch_overview | 1 | #28 |
| 10 | token_estimation | observability_telemetry | 1 | #40 |

---

## Confusion Analysis Notes

- **TP (True Positive)**: Expected feature X, got feature X
- **FP (False Positive)**: Got feature X, but expected Y (or fallback)
- **FN (False Negative)**: Expected feature X, got Y (or fallback)
- **Precision** = TP / (TP + FP)
- **Recall** = TP / (TP + FN)
- **F1** = 2 * (Precision * Recall) / (Precision + Recall)
