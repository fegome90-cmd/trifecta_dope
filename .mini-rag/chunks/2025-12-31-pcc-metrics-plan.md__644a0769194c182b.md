### Task 3: Extend eval-plan output with PCC metrics (TDD)

**Files:**
- Modify: `src/infrastructure/cli.py`
- Test: `tests/unit/test_pcc_metrics.py`

**Step 1: Add failing test for eval-plan PCC summary**

Append to `tests/unit/test_pcc_metrics.py`:
```python
from src.application.pcc_metrics import summarize_pcc


def test_summarize_pcc_counts() -> None:
    rows = [
        {"path_correct": True, "false_fallback": False, "safe_fallback": False},
        {"path_correct": False, "false_fallback": True, "safe_fallback": False},
    ]

    summary = summarize_pcc(rows)
    assert summary["path_correct_count"] == 1
    assert summary["false_fallback_count"] == 1
```

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/unit/test_pcc_metrics.py::test_summarize_pcc_counts -v
```
Expected: FAIL.

**Step 3: Implement summarize_pcc helper**

In `src/application/pcc_metrics.py`:
```python
def summarize_pcc(rows: list[dict[str, bool]]) -> dict[str, int]:
    return {
        "path_correct_count": sum(1 for r in rows if r.get("path_correct")),
        "false_fallback_count": sum(1 for r in rows if r.get("false_fallback")),
        "safe_fallback_count": sum(1 for r in rows if r.get("safe_fallback")),
    }
```

**Step 4: Update eval-plan to compute PCC metrics**
