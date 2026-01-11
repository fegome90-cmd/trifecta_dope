```bash
python - <<'PY'
from __future__ import annotations
import json
from pathlib import Path

baseline = json.loads(Path('/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/t9-3-4-baseline/tmp_plan_test/t9_3_4_baseline_tasks.json').read_text())
current = json.loads(Path('tmp_plan_test/t9_3_5_current_tasks.json').read_text())

baseline_map = {item['task_id']: item for item in baseline}
current_map = {item['task_id']: item for item in current}

rows = []
fp_baseline = fp_current = 0
fallback_baseline = fallback_current = 0
false_fallback = 0
obs_fp_baseline = obs_fp_current = 0

for task_id, b in baseline_map.items():
    c = current_map[task_id]
    expected = b['expected']
    b_pred = b['predicted']
    c_pred = c['predicted']

    if b_pred == 'fallback':
        fallback_baseline += 1
    if c_pred == 'fallback':
        fallback_current += 1

    if expected != 'fallback' and b_pred != expected:
        fp_baseline += 1
    if expected != 'fallback' and c_pred != expected:
        fp_current += 1

    if expected != 'fallback' and c_pred == 'fallback':
        false_fallback += 1

    if b_pred == 'observability_telemetry' and expected != 'observability_telemetry':
        obs_fp_baseline += 1
    if c_pred == 'observability_telemetry' and expected != 'observability_telemetry':
        obs_fp_current += 1

    if b['predicted'] != c['predicted'] or b['sele
