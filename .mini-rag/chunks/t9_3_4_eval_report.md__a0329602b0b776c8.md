### 1. Confusion Report Generation

**File**: `src/infrastructure/cli.py`

**New Function**: `_generate_confusion_report()`

```python
def _generate_confusion_report(
    results: list,
    expected_features: dict,
    dataset_path: Path,
    dataset_sha256: str,
    dataset_mtime: str,
    segment: str,
    output_path: str
) -> None:
    """Generate confusion report (T9.3.4)."""
    # Compute per-feature TP/FP/FN metrics
    # Track confusion pairs (expected → got)
    # Calculate precision, recall, F1
    # Save to docs/plans/t9_3_4_confusions.md
```

**Features**:
- Per-feature TP/FP/FN with precision/recall/F1
- Top 10 confusion pairs with example task IDs
- Dataset identity (SHA256, mtime, path)
- Run identity (commit hash, timestamp, segment)
