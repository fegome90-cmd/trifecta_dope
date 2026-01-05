### Task 1: Add PCC metrics helpers (TDD)

**Files:**
- Create: `src/application/pcc_metrics.py`
- Test: `tests/unit/test_pcc_metrics.py`

**Step 1: Write failing tests for PRIME feature_map parsing**

Create `tests/unit/test_pcc_metrics.py`:
```python
from pathlib import Path

from src.application.pcc_metrics import parse_feature_map


def test_parse_feature_map_paths(tmp_path: Path) -> None:
    prime = tmp_path / "prime_test.md"
    prime.write_text(
        """
### index.feature_map
| Feature | Chunk IDs | Paths | Keywords |
|---------|-----------|-------|----------|
| telemetry | `skill:*` | `README.md`, `src/infrastructure/telemetry.py` | telemetry |
| context_pack | `skill:*` | `src/application/use_cases.py` | context pack |
"""
    )

    feature_map = parse_feature_map(prime)

    assert feature_map["telemetry"] == ["README.md", "src/infrastructure/telemetry.py"]
    assert feature_map["context_pack"] == ["src/application/use_cases.py"]
```

**Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/unit/test_pcc_metrics.py::test_parse_feature_map_paths -v
```
Expected: FAIL (module/functions missing).

**Step 3: Implement minimal parser**

Create `src/application/pcc_metrics.py`:
