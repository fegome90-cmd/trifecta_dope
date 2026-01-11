```bash
uv run python - <<'PY'
from __future__ import annotations
import json
import re
from pathlib import Path
from unittest.mock import MagicMock

from src.application.plan_use_case import PlanUseCase

segment = Path('.')
dataset_path = Path('docs/plans/t9_plan_eval_tasks_v2_nl.md').resolve()
content = dataset_path.read_text()

tasks = re.findall(r'^\d+\.\s+"([^"]+)"', content, re.MULTILINE)
expected = {}
for line in content.split('\n'):
    match = re.match(r'^\d+\.\s+"([^"]+)"\s*\|\s*(\w+)', line)
    if match:
        expected[match.group(1)] = match.group(2)

use_case = PlanUseCase(MagicMock(), None)

tp = fp = fn = 0
for task in tasks:
    result = use_case.execute(segment, task)
    predicted = result.get('selected_feature') if result.get('plan_hit') else None
    pred = predicted or 'fallback'
    exp = expected.get(task, 'fallback')

    if pred == 'observability_telemetry' and exp == 'observability_telemetry':
        tp += 1
    elif pred == 'observability_telemetry' and exp != 'observability_telemetry':
        fp += 1
    elif pred != 'observability_telemetry' and exp == 'observability_telemetry':
        fn += 1

precision = tp / (tp + fp) if (tp + fp) else 0.0

Path('tmp_plan_test/t9_3_6_observability_metrics.json').write_text(
    json.dumps({'tp': tp, 'fp': fp, 'fn': fn, 'precision': precision}, indent=2)
)
PY
```
Expected: metrics JSON created.

---
