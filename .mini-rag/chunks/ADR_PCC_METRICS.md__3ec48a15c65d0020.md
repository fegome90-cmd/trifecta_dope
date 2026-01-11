### Per-Task Evaluation

For each task in the dataset:

```python
evaluate_pcc(
    expected_feature=<from dataset>,
    predicted_feature=<from eval-plan result>,
    predicted_paths=<from eval-plan result>,
    feature_map=<from PRIME>,
    selected_by=<from eval-plan result>
)
# Returns: {path_correct, false_fallback, safe_fallback}
```
