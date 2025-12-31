## Confusion Analysis Notes

- **TP (True Positive)**: Expected feature X, got feature X
- **FP (False Positive)**: Got feature X, but expected Y (or fallback)
- **FN (False Negative)**: Expected feature X, got Y (or fallback)
- **Precision** = TP / (TP + FP) — of all predictions for X, how many were correct
- **Recall** = TP / (TP + FN) — of all actual X, how many were correctly predicted
- **F1** = 2 * (Precision * Recall) / (Precision + Recall)
