```python
def evaluate_pcc(
    expected_feature: str,
    predicted_feature: str | None,
    predicted_paths: list[str],
    feature_map: dict[str, list[str]],
    selected_by: str,
) -> dict[str, bool]:
    expected_paths = feature_map.get(expected_feature, []) if expected_feature != "fallback" else []
    path_correct = bool(
        expected_feature != "fallback"
        and predicted_feature == expected_feature
        and any(p in expected_paths for p in predicted_paths)
    )

    false_fallback = expected_feature != "fallback" and selected_by == "fallback"
    safe_fallback = expected_feature == "fallback" and selected_by == "fallback"

    return {
        "path_correct": path_correct,
        "false_fallback": false_fallback,
        "safe_fallback": safe_fallback,
    }
```

**Step 4: Run test to verify it passes**

Run:
```bash
uv run pytest tests/unit/test_pcc_metrics.py::test_evaluate_pcc_path_correctness -v
```
Expected: PASS.

**Step 5: Commit**

```bash
git add src/application/pcc_metrics.py tests/unit/test_pcc_metrics.py
git commit -m "feat: add PCC evaluation helper"
```

---
