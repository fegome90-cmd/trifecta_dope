## Confusion Analysis Notes

- **TP (True Positive)**: Expected feature X, got feature X
- **FP (False Positive)**: Got feature X, but expected Y (or fallback)
- **FN (False Negative)**: Expected feature X, got Y (or fallback)
- **Precision** = TP / (TP + FP)
- **Recall** = TP / (TP + FN)
- **F1** = 2 * (Precision * Recall) / (Precision + Recall)
