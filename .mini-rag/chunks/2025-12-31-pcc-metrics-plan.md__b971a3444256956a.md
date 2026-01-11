### Task 2: Compute PCC metrics per task (TDD)

**Files:**
- Modify: `src/application/pcc_metrics.py`
- Test: `tests/unit/test_pcc_metrics.py`

**Step 1: Add failing test for PCC evaluation**

Append to `tests/unit/test_pcc_metrics.py`:
```python
from src.application.pcc_metrics import evaluate_pcc


def test_evaluate_pcc_path_correctness() -> None:
    feature_map = {"telemetry": ["src/infrastructure/telemetry.py"]}

    result = evaluate_pcc(
        expected_feature="telemetry",
        predicted_feature="telemetry",
        predicted_paths=["src/infrastructure/telemetry.py"],
        feature_map=feature_map,
        selected_by="nl_trigger",
    )

    assert result["path_correct"] is True
    assert result["false_fallback"] is False
    assert result["safe_fallback"] is False
```

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/unit/test_pcc_metrics.py::test_evaluate_pcc_path_correctness -v
```
Expected: FAIL.

**Step 3: Implement minimal PCC evaluation**

In `src/application/pcc_metrics.py`:
