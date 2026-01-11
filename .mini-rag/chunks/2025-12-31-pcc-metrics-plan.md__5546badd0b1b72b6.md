```python
from __future__ import annotations

from pathlib import Path


def parse_feature_map(prime_path: Path) -> dict[str, list[str]]:
    content = prime_path.read_text()
    lines = content.splitlines()
    feature_map: dict[str, list[str]] = {}

    in_table = False
    for line in lines:
        if line.strip().startswith("### index.feature_map"):
            in_table = True
            continue
        if in_table and line.strip().startswith("### "):
            break
        if in_table and line.strip().startswith("|") and "Feature" not in line:
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) >= 3:
                feature = cols[0]
                paths_raw = cols[2]
                paths = [p.strip().strip("`") for p in paths_raw.split(",") if p.strip()]
                feature_map[feature] = paths

    return feature_map
```

**Step 4: Run test to verify it passes**

Run:
```bash
uv run pytest tests/unit/test_pcc_metrics.py::test_parse_feature_map_paths -v
```
Expected: PASS.

**Step 5: Commit**

```bash
git add src/application/pcc_metrics.py tests/unit/test_pcc_metrics.py
git commit -m "feat: add PCC feature_map parser"
```

---
