```bash
uv run python - <<'PY'
from __future__ import annotations
import json
import re
from pathlib import Path
from unittest.mock import MagicMock

from src.application.plan_use_case import PlanUseCase

segment = Path('.')
dataset_path = Path('/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/t9-3-6-clamp-calibration/docs/plans/t9_plan_eval_tasks_v2_nl.md').resolve()
content = dataset_path.read_text()

tasks = re.findall(r'^\d+\.\s+"([^"]+)"', content, re.MULTILINE)
expected = {}
for line in content.split('\n'):
    match = re.match(r'^\d+\.\s+"([^"]+)"\s*\|\s*(\w+)', line)
    if match:
        expected[match.group(1)] = match.group(2)

use_case = PlanUseCase(MagicMock(), None)
results = []
for idx, task in enumerate(tasks, 1):
    result = use_case.execute(segment, task)
    selected = result.get('selected_feature') if result.get('plan_hit') else None
    predicted = selected or 'fallback'
    results.append({
        'task_id': idx,
        'task': task,
        'expected': expected.get(task, 'fallback'),
        'predicted': predicted,
        'selected_by': result.get('selected_by', 'fallback'),
    })

Path('tmp_plan_test/t9_3_4_baseline_tasks.json').write_text(json.dumps(results, indent=2))
PY
```

Current worktree:
