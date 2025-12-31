# T9.3.6 Clamp Calibration + Stabilization (Router v1) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Produce a clamp impact report, calibrate the single-word clamp via config-driven support terms, re-evaluate against the same dataset, and freeze Router v1 via ADR.

**Architecture:** Keep L2 matching deterministic with score/specificity/priority ordering and tie-to-fallback. Move support term checks into aliases.yaml for observability_telemetry only, and emit explicit telemetry fields for clamp decisions.

**Tech Stack:** Python 3.12+, Typer CLI, Pytest, uv, Markdown docs.

---

### Task 1: Capture T9.3.4 vs T9.3.5 baselines (no dataset changes)

**Files:**
- Read: `docs/plans/t9_plan_eval_tasks_v2_nl.md`
- Create: `tmp_plan_test/t9_3_4_baseline.txt`
- Create: `tmp_plan_test/t9_3_5_current.txt`
- Create: `tmp_plan_test/t9_3_4_baseline_tasks.json`
- Create: `tmp_plan_test/t9_3_5_current_tasks.json`

**Step 1: Verify dataset identity (no edits)**

Run:
```bash
sha256sum docs/plans/t9_plan_eval_tasks_v2_nl.md
```
Expected: hash remains constant throughout.

**Step 2: Run baseline eval (T9.3.4)**

From `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/t9-3-4-baseline`:
```bash
uv run trifecta ctx eval-plan -s . --dataset /Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/t9-3-6-clamp-calibration/docs/plans/t9_plan_eval_tasks_v2_nl.md \
  | tee tmp_plan_test/t9_3_4_baseline.txt
```
Expected: `EVALUATION REPORT: ctx.plan` output and file created.

**Step 3: Run current eval (T9.3.5)**

From `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/.worktrees/t9-3-6-clamp-calibration`:
```bash
uv run trifecta ctx eval-plan -s . --dataset docs/plans/t9_plan_eval_tasks_v2_nl.md \
  | tee tmp_plan_test/t9_3_5_current.txt
```
Expected: `EVALUATION REPORT: ctx.plan` output and file created.

**Step 4: Generate per-task predictions (baseline + current)**

Baseline worktree:
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

Path('tmp_plan_test/t9_3_5_current_tasks.json').write_text(json.dumps(results, indent=2))
PY
```

---

### Task 2: Clamp Impact Report (diff-based, evidence-only)

**Files:**
- Create: `docs/plans/t9_3_6_clamp_calibration.md`

**Step 1: Generate changed-task table + metrics**

Run from current worktree:
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

    if b['predicted'] != c['predicted'] or b['selected_by'] != c['selected_by']:
        rows.append({
            'task_id': task_id,
            'task': b['task'],
            'expected': expected,
            'baseline_predicted': b_pred,
            'current_predicted': c_pred,
            'transition': f"{b['selected_by']}->{c['selected_by']}",
            'was_fp_before': expected != 'fallback' and b_pred != expected,
            'is_false_fallback_now': expected != 'fallback' and c_pred == 'fallback',
        })

summary = {
    'fp_baseline': fp_baseline,
    'fp_current': fp_current,
    'fp_reduction': fp_baseline - fp_current,
    'fallback_baseline': fallback_baseline,
    'fallback_current': fallback_current,
    'fallback_increase': fallback_current - fallback_baseline,
    'false_fallback_current': false_fallback,
    'net_impact': (fp_baseline - fp_current) - false_fallback,
    'observability_fp_baseline': obs_fp_baseline,
    'observability_fp_current': obs_fp_current,
}

Path('tmp_plan_test/t9_3_6_clamp_delta.json').write_text(json.dumps({'rows': rows, 'summary': summary}, indent=2))
PY
```
Expected: `tmp_plan_test/t9_3_6_clamp_delta.json` created.

**Step 2: Write Clamp Impact Report doc**

Manually create `docs/plans/t9_3_6_clamp_calibration.md` with:
- Clamp Impact Report section
- Literal per-task table for changed tasks only
- Summary metrics + observability_telemetry FP baseline/current
- Literal eval outputs pasted from `tmp_plan_test/t9_3_4_baseline.txt` and `tmp_plan_test/t9_3_5_current.txt`

---

### Task 3: Calibrate clamp (config-driven support terms)

**Files:**
- Modify: `_ctx/aliases.yaml`
- Modify: `src/application/plan_use_case.py`
- Modify: `tests/test_plan_use_case.py`

**Step 1: Add failing tests (TDD)**

Add tests in `tests/test_plan_use_case.py`:
```python
def test_l2_single_word_requires_support_terms(mock_filesystem, mock_telemetry, tmp_path):
    ctx_dir = tmp_path / "_ctx"
    ctx_dir.mkdir()
    aliases = {
        "schema_version": 3,
        "features": {
            "observability_telemetry": {
                "priority": 4,
                "nl_triggers": ["telemetry"],
                "support_terms": ["stats", "metrics"],
                "bundle": {"chunks": ["c1"], "paths": ["p1.py"]},
            }
        },
    }
    (ctx_dir / "aliases.yaml").write_text(json.dumps(aliases))
    (tmp_path / "p1.py").write_text("# p1")
    (ctx_dir / "prime_test.md").write_text(
        "# Test\n## [INDEX]\n### index.entrypoints\n| Path | Razn |\n|------|-------|\n| `README.md` | Entry |"
    )

    use_case = PlanUseCase(mock_filesystem, mock_telemetry)
    blocked = use_case.execute(tmp_path, "telemetry")
    allowed = use_case.execute(tmp_path, "telemetry stats")

    assert blocked["selected_by"] == "fallback"
    assert blocked["l2_warning"] == "weak_single_word_trigger"
    assert allowed["selected_by"] == "nl_trigger"


def test_l2_support_terms_telemetry_fields(mock_filesystem, mock_telemetry, tmp_path):
    ctx_dir = tmp_path / "_ctx"
    ctx_dir.mkdir()
    aliases = {
        "schema_version": 3,
        "features": {
            "observability_telemetry": {
                "priority": 4,
                "nl_triggers": ["telemetry"],
                "support_terms": ["stats"],
                "bundle": {"chunks": ["c1"], "paths": ["p1.py"]},
            }
        },
    }
    (ctx_dir / "aliases.yaml").write_text(json.dumps(aliases))
    (tmp_path / "p1.py").write_text("# p1")
    (ctx_dir / "prime_test.md").write_text(
        "# Test\n## [INDEX]\n### index.entrypoints\n| Path | Razn |\n|------|-------|\n| `README.md` | Entry |"
    )

    use_case = PlanUseCase(mock_filesystem, mock_telemetry)
    result = use_case.execute(tmp_path, "telemetry stats")

    assert result["l2_support_terms_required"] is True
    assert result["l2_support_terms_present"] == ["stats"]
    assert result["l2_weak_single_word_trigger"] is False
    assert result["l2_clamp_decision"] == "allow"
```

**Step 2: Run tests to confirm failure**

Run:
```bash
uv run pytest tests/test_plan_use_case.py::test_l2_single_word_requires_support_terms -v
uv run pytest tests/test_plan_use_case.py::test_l2_support_terms_telemetry_fields -v
```
Expected: FAIL (fields not present + config not honored yet).

**Step 3: Update aliases config**

Add to `_ctx/aliases.yaml` under `observability_telemetry`:
```yaml
    support_terms:
      - stats
      - metrics
      - events
      - jsonl
      - latency
      - p95
      - p50
      - flush
```

**Step 4: Implement config-driven support terms + telemetry**

Update `src/application/plan_use_case.py`:
- Remove hardcoded support_terms list
- For single-word triggers (priority >= 4), require `support_terms` in feature config
- If no support term present: fallback with warning `weak_single_word_trigger`
- Emit telemetry fields:
  - `l2_support_terms_required` (bool)
  - `l2_support_terms_present` (list)
  - `l2_weak_single_word_trigger` (bool)
  - `l2_clamp_decision` ("allow"|"block")

**Step 5: Run tests to confirm pass**

Run:
```bash
uv run pytest tests/test_plan_use_case.py::test_l2_single_word_requires_support_terms -v
uv run pytest tests/test_plan_use_case.py::test_l2_support_terms_telemetry_fields -v
```
Expected: PASS.

---

### Task 4: Re-eval T9.3.6 (same dataset)

**Files:**
- Create: `tmp_plan_test/t9_3_6_after.txt`

**Step 1: Run eval-plan**

Run:
```bash
uv run trifecta ctx eval-plan -s . --dataset docs/plans/t9_plan_eval_tasks_v2_nl.md \
  | tee tmp_plan_test/t9_3_6_after.txt
```
Expected: `EVALUATION REPORT: ctx.plan` output and file created.

**Step 2: Compute observability_telemetry metrics**

Run:
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

### Task 5: Update T9.3.6 report with literal outputs

**Files:**
- Modify: `docs/plans/t9_3_6_clamp_calibration.md`

**Step 1: Add re-eval section**

Update the doc with:
- Before/after table (T9.3.5 vs T9.3.6) for key metrics
- Literal output pasted from `tmp_plan_test/t9_3_6_after.txt`
- Observability telemetry TP/FP/FN + precision from `tmp_plan_test/t9_3_6_observability_metrics.json`
- Confirm targets vs thresholds

---

### Task 6: ADR freeze for Router v1

**Files:**
- Create: `docs/adr/ADR_T9_ROUTER_V1.md`

**Step 1: Create ADR content**

Include:
- Scope: Router v1 for ctx.plan (PCC-only)
- Invariants: determinism, tie->fallback, true_zero_guidance=0, bundle assertions behavior
- Matching levels: L1/L2/L3/L4 definitions
- Scoring: exact=2, subset=1 + specificity + priority ordering
- Clamp: single-word support_terms rule (config-driven)
- Warnings taxonomy: weak_single_word_trigger, ambiguous_single_word_triggers, match_tie_fallback, bundle_assert_failed
- Gates: Core Gate-NL + Quality Gate (metrics + thresholds)
- Frozen for T10: changes require ADR update + re-run gates

---

### Task 7: Full test sweep + commit

**Files:**
- Modify: `_ctx/aliases.yaml`
- Modify: `src/application/plan_use_case.py`
- Modify: `tests/test_plan_use_case.py`
- Modify: `docs/plans/t9_3_6_clamp_calibration.md`
- Create: `docs/adr/ADR_T9_ROUTER_V1.md`

**Step 1: Run full test suite**

Run:
```bash
uv run pytest
```
Expected: PASS.

**Step 2: Commit**

Run:
```bash
git add _ctx/aliases.yaml src/application/plan_use_case.py tests/test_plan_use_case.py \
  docs/plans/t9_3_6_clamp_calibration.md docs/adr/ADR_T9_ROUTER_V1.md

git commit -m "feat: calibrate clamp and freeze Router v1"
```

---

Plan complete and saved to `docs/plans/2025-12-31-t9-3-6-clamp-calibration-plan.md`. Two execution options:

1. Subagent-Driven (this session) — I dispatch a fresh subagent per task, review between tasks, fast iteration
2. Parallel Session (separate) — Open new session with executing-plans, batch execution with checkpoints

Which approach?
