# T9.3.4 Confusion Report

**Generated**: 2025-12-31T14:40:28.246017

---

## Dataset Identity

- **Path**: `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/docs/plans/t9_plan_eval_tasks_v2_nl.md`
- **SHA256**: `610e7bc4ebf14ad2`
- **mtime**: `2025-12-31T14:10:24.794518`

---

## Run Identity

- **Segment**: `.`
- **Commit**: `3611eae`
- **Timestamp**: `2025-12-31T14:40:28.246017`

---

## Per-Feature Metrics (TP/FP/FN)

| Feature | TP | FP | FN | Precision | Recall | F1 |
|---------|----|----|----|-----------|--------|----|
| fallback | 6 | 1 | 3 | 0.86 | 0.67 | 0.75 |
| observability_telemetry | 5 | 4 | 2 | 0.56 | 0.71 | 0.63 |
| context_pack | 5 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| symbol_surface | 2 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| token_estimation | 2 | 0 | 1 | 1.00 | 0.67 | 0.80 |
| arch_overview | 2 | 1 | 0 | 0.67 | 1.00 | 0.80 |
| cli_commands | 2 | 2 | 0 | 0.50 | 1.00 | 0.67 |
| prime_indexing | 2 | 0 | 1 | 1.00 | 0.67 | 0.80 |
| get_chunk_use_case | 1 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| telemetry_flush | 1 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| directory_listing | 1 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| import_statements | 1 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| chunk_retrieval_flow | 1 | 0 | 0 | 1.00 | 1.00 | 1.00 |
| code_navigation | 1 | 0 | 1 | 1.00 | 0.50 | 0.67 |

---

## Top Confusions (Expected → Got)

Top 10 confusion pairs by frequency:

| Rank | Expected | Got | Count | Example Task IDs |
|------|----------|-----|-------|-------------------|
| 1 | fallback | observability_telemetry | 2 | #4, #8 |
| 2 | observability_telemetry | cli_commands | 1 | #19 |
| 3 | observability_telemetry | fallback | 1 | #25 |
| 4 | prime_indexing | arch_overview | 1 | #28 |
| 5 | fallback | cli_commands | 1 | #30 |
| 6 | code_navigation | observability_telemetry | 1 | #34 |
| 7 | token_estimation | observability_telemetry | 1 | #40 |

---

## Confusion Analysis Notes

- **TP (True Positive)**: Expected feature X, got feature X
- **FP (False Positive)**: Got feature X, but expected Y (or fallback)
- **FN (False Negative)**: Expected feature X, got Y (or fallback)
- **Precision** = TP / (TP + FP) — of all predictions for X, how many were correct
- **Recall** = TP / (TP + FN) — of all actual X, how many were correctly predicted
- **F1** = 2 * (Precision * Recall) / (Precision + Recall)
