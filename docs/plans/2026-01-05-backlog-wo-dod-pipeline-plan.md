# Backlog + Work Orders + DoD Pipeline Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement a YAML-backed backlog + work order pipeline with DoD enforcement, reproducible verification, and epic -> WO -> DoD traceability under `trifecta_dope/_ctx/`.

**Architecture:** Canonical backlog lives in `_ctx/backlog/backlog.yaml`, DoD catalog in `_ctx/dod/*.yaml`, and operational WOs in `_ctx/jobs/{pending,running,done,failed}`. JSON Schema validates YAMLs, scripts enforce lifecycle, logs/handoffs are stored in `_ctx/logs/` and `_ctx/handoff/`. Existing `_ctx/blacklog` is renamed to `_ctx/backlog`; a legacy stub may remain at `_ctx/blacklog/README.md` and is excluded from validation.

**Tech Stack:** Python 3, jsonschema, ruamel.yaml, PyYAML, bash, git, pytest.

---

## Phase 1 - Schema Design

**Deliverables**
- `docs/backlog/schema/backlog.schema.json`
- `docs/backlog/schema/work_order.schema.json`
- `docs/backlog/schema/dod.schema.json`
- `docs/backlog/README.md`
- `scripts/ctx_backlog_validate.py`
- `_ctx/backlog/backlog.yaml` (renamed from `_ctx/blacklog/blacklog.yaml`)
- `_ctx/dod/dod-default.yaml` (renamed from `_ctx/dod/dod.yaml`)

**Acceptance Criteria**
- `backlog.yaml` validates with `backlog.schema.json`.
- All `_ctx/jobs/pending/*.yaml` validate with `work_order.schema.json`.
- Every WO references an existing `epic_id` and `dod_id`.
- Every WO includes `verify.commands[]` and `scope.allow[]/scope.deny[]`.
- No references to `blacklog` outside `_ctx/blacklog/README.md`.

**Metrics**
- Schema pass rate: 100%.
- Validation time: < 1s per WO on local run.

**Rollback**
- Revert commit(s) for schema/docs/scripts.

### Task 1: Add YAML/schema dependencies

**Files:**
- Modify: `pyproject.toml`
- Modify: `uv.lock`
- Test: `tests/unit/test_ctx_dependencies.py`

**Step 1: Write the failing test**

```python
from importlib import import_module

def test_ctx_dependencies_import():
    for module in ("ruamel.yaml", "yaml", "jsonschema"):
        import_module(module)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest -q tests/unit/test_ctx_dependencies.py`
Expected: FAIL with `ModuleNotFoundError`.

**Step 3: Add dependencies**

Add to `pyproject.toml`:
- `ruamel.yaml`
- `PyYAML`
- `jsonschema`

Sync lockfile: `uv sync`

**Step 4: Run test to verify it passes**

Run: `uv run pytest -q tests/unit/test_ctx_dependencies.py`
Expected: PASS.

**Step 5: Commit**

```bash
git add pyproject.toml uv.lock tests/unit/test_ctx_dependencies.py
git commit -m "build: add ctx yaml/schema deps"
```

### Task 2: Rename blacklog -> backlog and update references

**Files:**
- Move: `_ctx/blacklog/` -> `_ctx/backlog/`
- Create: `_ctx/blacklog/README.md` (legacy stub)
- Test: `tests/unit/test_ctx_backlog_layout.py`

**Step 1: Write the failing test**

```python
from pathlib import Path

def test_backlog_layout():
    assert Path("_ctx/backlog").exists()
    legacy = Path("_ctx/blacklog")
    if legacy.exists():
        assert legacy.is_dir()
        assert (legacy / "README.md").exists()
        extra = {p.name for p in legacy.iterdir()} - {"README.md"}
        assert not extra
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest -q tests/unit/test_ctx_backlog_layout.py`
Expected: FAIL because `_ctx/backlog` does not exist.

**Step 3: Rename directory and update references**

```bash
mv _ctx/blacklog _ctx/backlog
mkdir -p _ctx/blacklog
cat <<'EOF' > _ctx/blacklog/README.md
Legacy stub. Backlog moved to _ctx/backlog.
EOF
rg -n "blacklog" -g"*" _ctx docs scripts || true
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest -q tests/unit/test_ctx_backlog_layout.py`
Expected: PASS.

**Step 5: Commit**

```bash
git add _ctx/backlog tests/unit/test_ctx_backlog_layout.py
git commit -m "chore: rename blacklog to backlog"
```

### Task 3: Add JSON Schemas for backlog, work orders, and DoD

**Files:**
- Create: `docs/backlog/schema/backlog.schema.json`
- Create: `docs/backlog/schema/work_order.schema.json`
- Create: `docs/backlog/schema/dod.schema.json`
- Test: `tests/unit/test_ctx_schemas.py`

**Step 1: Write the failing test**

```python
from pathlib import Path
import json
import yaml
from jsonschema import validate

BACKLOG = Path("_ctx/backlog/backlog.yaml")
SCHEMA = Path("docs/backlog/schema/backlog.schema.json")


def test_backlog_schema():
    data = yaml.safe_load(BACKLOG.read_text())
    schema = json.loads(SCHEMA.read_text())
    validate(instance=data, schema=schema)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest -q tests/unit/test_ctx_schemas.py`
Expected: FAIL because schema file is missing or invalid.

**Step 3: Write schemas**

Implement JSON Schemas with:
- `version` as integer
- `epics[]` with required fields
- `work_orders` optional extensions via `x_*`
- `additionalProperties: false` with `patternProperties` for `^x_`
- `scope.allow/deny` arrays

**Step 4: Run test to verify it passes**

Run: `uv run pytest -q tests/unit/test_ctx_schemas.py`
Expected: PASS.

**Step 5: Commit**

```bash
git add docs/backlog/schema tests/unit/test_ctx_schemas.py
git commit -m "docs: add backlog/work-order/dod schemas"
```

### Task 4: Add docs/backlog/README.md

**Files:**
- Create: `docs/backlog/README.md`

**Step 1: Write the failing test**

```python
from pathlib import Path

def test_backlog_readme_exists():
    assert Path("docs/backlog/README.md").exists()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest -q tests/unit/test_ctx_backlog_readme.py`
Expected: FAIL because README does not exist.

**Step 3: Write README**

Include:
- State machine (pending/running/done/failed)
- Traceability invariants
- Rollback notes

**Step 4: Run test to verify it passes**

Run: `uv run pytest -q tests/unit/test_ctx_backlog_readme.py`
Expected: PASS.

**Step 5: Commit**

```bash
git add docs/backlog/README.md tests/unit/test_ctx_backlog_readme.py
git commit -m "docs: add backlog pipeline readme"
```

### Task 5: Implement scripts/ctx_backlog_validate.py

**Files:**
- Create: `scripts/ctx_backlog_validate.py`
- Create: `tests/fixtures/ctx/backlog.yaml`
- Create: `tests/fixtures/ctx/wo.yaml`
- Create: `tests/fixtures/ctx/dod.yaml`
- Test: `tests/unit/test_ctx_backlog_validate.py`

**Step 1: Write the failing test**

```python
import subprocess

def test_ctx_backlog_validate_ok():
    result = subprocess.run(
        ["python", "scripts/ctx_backlog_validate.py", "--fixtures"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest -q tests/unit/test_ctx_backlog_validate.py`
Expected: FAIL because script does not exist.

**Step 3: Implement validator**

Behavior:
- Load `_ctx/backlog/backlog.yaml` and `_ctx/dod/*.yaml`
- Define canonical set: `_ctx/backlog/backlog.yaml`, `_ctx/dod/*.yaml`, `_ctx/jobs/{pending,running,done,failed}/*.yaml`
- Ignore `_ctx/**/legacy/**` by default
- Validate against schemas
- Validate `epic_id` and `dod_id` references
- Validate scope fields exist in each WO
- `--root <dir>` overrides repo root; `--fixtures` uses `tests/fixtures/ctx/` as root

**Step 4: Run test to verify it passes**

Run: `uv run pytest -q tests/unit/test_ctx_backlog_validate.py`
Expected: PASS.

**Step 5: Commit**

```bash
git add scripts/ctx_backlog_validate.py tests/fixtures/ctx tests/unit/test_ctx_backlog_validate.py
git commit -m "feat: add backlog validator script"
```

---

## Phase 2 - Data Migration

**Deliverables**
- `_ctx/backlog/backlog.yaml` populated with real epics
- `_ctx/jobs/pending/WO-0004.yaml`
- `_ctx/jobs/pending/WO-0005.yaml`
- `docs/backlog/MIGRATION.md`

**Acceptance Criteria**
- 100% epics migrated with `status`, `priority`, `outcome`.
- Each P0 epic has at least one WO in `wo_queue`.
- Validator passes locally.

**Metrics**
- Coverage: 100% of known epics in backlog.
- % WOs with verify commands: 100%.

**Rollback**
- Keep source snapshots under `docs/backlog/legacy/`.
- Revert commit if needed.

### Task 6: Migrate existing backlog sources into canonical files

**Files:**
- Move: `_ctx/backlog/central_telefonica/central_telefonica_v0.1.yaml` -> `docs/backlog/legacy/inputs/central_telefonica_v0.1.yaml`
- Create: `_ctx/backlog/backlog.yaml`
- Create: `docs/backlog/MIGRATION.md`
- Test: `tests/unit/test_ctx_backlog_migration.py`

**Step 1: Write the failing test**

```python
from pathlib import Path

def test_backlog_yaml_exists():
    assert Path("_ctx/backlog/backlog.yaml").exists()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest -q tests/unit/test_ctx_backlog_migration.py`
Expected: FAIL because backlog.yaml does not exist.

**Step 3: Implement migration**

Rules:
- Copy epic list from `docs/backlog/legacy/inputs/central_telefonica_v0.1.yaml` into `_ctx/backlog/backlog.yaml`.
- Ensure `wo_queue` lists `WO-0004`, `WO-0005`.
- Record mapping in `docs/backlog/MIGRATION.md`.

**Step 4: Run test to verify it passes**

Run: `uv run pytest -q tests/unit/test_ctx_backlog_migration.py`
Expected: PASS.

**Step 5: Commit**

```bash
git add _ctx/backlog/backlog.yaml docs/backlog/legacy/inputs/central_telefonica_v0.1.yaml docs/backlog/MIGRATION.md tests/unit/test_ctx_backlog_migration.py
git commit -m "docs: migrate backlog into canonical yaml"
```

### Task 7: Create initial pending WOs (WO-0004, WO-0005)

**Files:**
- Create: `_ctx/jobs/pending/WO-0004.yaml`
- Create: `_ctx/jobs/pending/WO-0005.yaml`
- Test: `tests/unit/test_ctx_pending_wos.py`

**Step 1: Write the failing test**

```python
from pathlib import Path

def test_pending_wos_exist():
    assert Path("_ctx/jobs/pending/WO-0004.yaml").exists()
    assert Path("_ctx/jobs/pending/WO-0005.yaml").exists()
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest -q tests/unit/test_ctx_pending_wos.py`
Expected: FAIL because files do not exist.

**Step 3: Create WO YAMLs**

Include deliverables that reference:
- `tests/integration/test_ctx_search_linter_ab_controlled.py`
- `docs/reports/KNOWN_FAILS.md`
- `_ctx/logs/ab_off.log`
- `_ctx/logs/ab_on.log`

**Step 4: Run test to verify it passes**

Run: `uv run pytest -q tests/unit/test_ctx_pending_wos.py`
Expected: PASS.

**Step 5: Commit**

```bash
git add _ctx/jobs/pending/WO-0004.yaml _ctx/jobs/pending/WO-0005.yaml tests/unit/test_ctx_pending_wos.py
git commit -m "docs: add initial pending work orders"
```

---

## Phase 3 - Work Order Execution

**Deliverables**
- `scripts/ctx_wo_take.py`
- `scripts/ctx_verify_run.sh`
- `scripts/ctx_handoff_pack.sh`
- `scripts/ctx_wo_finish.py`
- `scripts/ctx_scope_lint.py`
- `scripts/ctx_reconcile_state.py`

**Acceptance Criteria**
- `wo_take` creates worktree/branch, updates status to running, writes lock.
- `verify_run` runs commands, writes `_ctx/logs/<WO>/`, and emits `verdict.json`.
- `handoff_pack` creates `_ctx/handoff/<WO>/` with required artifacts.
- `wo_finish` blocks `done` if DoD artifacts are missing.

**Metrics**
- % WOs passing verify in one try.
- Median lead time from take -> done.

**Rollback**
- Revert scripts; use `scripts/ctx_reconcile_state.py` if needed.
`ctx_reconcile_state.py` is the canonical repair tool; any manual recovery outside it is an incident.

### Task 8: Implement ctx_wo_take.py

**Files:**
- Create: `scripts/ctx_wo_take.py`
- Test: `tests/unit/test_ctx_wo_take.py`

**Step 1: Write the failing test**

```python
import subprocess

def test_wo_take_help():
    result = subprocess.run([
        "python", "scripts/ctx_wo_take.py", "--help"
    ], capture_output=True, text=True)
    assert result.returncode == 0
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest -q tests/unit/test_ctx_wo_take.py`
Expected: FAIL because script does not exist.

**Step 3: Implement script**

Behavior:
- Validate WO schema
- Ensure epic_id exists
- Create worktree and branch
- Move WO pending -> running, set `owner`, `started_at`
- Write `_ctx/jobs/running/<WO>.lock`

**Step 4: Run test to verify it passes**

Run: `uv run pytest -q tests/unit/test_ctx_wo_take.py`
Expected: PASS.

**Step 5: Commit**

```bash
git add scripts/ctx_wo_take.py tests/unit/test_ctx_wo_take.py
git commit -m "feat: add wo take script"
```

### Task 9: Implement ctx_verify_run.sh + scope lint

**Files:**
- Create: `scripts/ctx_verify_run.sh`
- Create: `scripts/ctx_scope_lint.py`
- Test: `tests/unit/test_ctx_verify_run.py`

**Step 1: Write the failing test**

```python
import subprocess

def test_verify_run_help():
    result = subprocess.run(["bash", "scripts/ctx_verify_run.sh", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest -q tests/unit/test_ctx_verify_run.py`
Expected: FAIL because script does not exist.

**Step 3: Implement scripts**

Behavior:
- `set -euo pipefail`
- Read `verify.commands[]` from WO
- Run each command, capture stdout/stderr to `_ctx/logs/<WO>/<cmd>.log`
- Generate `verdict.json` with PASS/FAIL, timestamps, wo_id, epic_id, dod_id, git_commit
- Run scope lint against `scope.allow/deny` before verdict

**Step 4: Run test to verify it passes**

Run: `uv run pytest -q tests/unit/test_ctx_verify_run.py`
Expected: PASS.

**Step 5: Commit**

```bash
git add scripts/ctx_verify_run.sh scripts/ctx_scope_lint.py tests/unit/test_ctx_verify_run.py
git commit -m "feat: add verify runner and scope lint"
```

### Task 10: Implement ctx_handoff_pack.sh

**Files:**
- Create: `scripts/ctx_handoff_pack.sh`
- Test: `tests/unit/test_ctx_handoff_pack.py`

**Step 1: Write the failing test**

```python
import subprocess

def test_handoff_pack_help():
    result = subprocess.run(["bash", "scripts/ctx_handoff_pack.sh", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest -q tests/unit/test_ctx_handoff_pack.py`
Expected: FAIL because script does not exist.

**Step 3: Implement script**

Behavior:
- Generate `diff.patch`, `diffstat.txt`, `status.txt`
- Copy logs required by DoD
- Render `handoff.md` from template

**Step 4: Run test to verify it passes**

Run: `uv run pytest -q tests/unit/test_ctx_handoff_pack.py`
Expected: PASS.

**Step 5: Commit**

```bash
git add scripts/ctx_handoff_pack.sh tests/unit/test_ctx_handoff_pack.py
git commit -m "feat: add handoff pack script"
```

### Task 11a: Implement ctx_reconcile_state.py (TDD)

**Files:**
- Create: `scripts/ctx_reconcile_state.py`
- Create: `tests/fixtures/reconcile/`
- Test: `tests/unit/test_ctx_reconcile_state.py`

**Acceptance Criteria**
- No destructive changes by default; `--apply` required to mutate.
- `stdout` prints a human summary; `--json out.json` writes machine-readable report.
- Detects at least: `RUNNING_WITHOUT_LOCK`, `LOCK_WITHOUT_RUNNING_WO`, `RUNNING_WO_WITHOUT_WORKTREE`, `WORKTREE_WITHOUT_RUNNING_WO`, `DUPLICATE_WO_ID`, `WO_INVALID_SCHEMA`.
- With `--apply`, only safe corrections are allowed (regenerate lock from WO). Moving WO to `failed` requires `--force` and `x_reconcile_reason`.
- Detects `DUPLICATE_WO_ID` across all WO states and marks it severity `P0` with non-zero exit.
- Detects `WO_INVALID_SCHEMA`; with `--apply` it refuses to mutate and exits non-zero.

**Step 1: Write the failing test**

```python
import subprocess

def test_reconcile_detects_running_without_lock():
    result = subprocess.run(
        ["python", "scripts/ctx_reconcile_state.py", "--fixtures", "running_without_lock"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "RUNNING_WITHOUT_LOCK" in result.stdout

def test_reconcile_detects_lock_without_running_wo():
    result = subprocess.run(
        ["python", "scripts/ctx_reconcile_state.py", "--fixtures", "lock_without_running_wo"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "LOCK_WITHOUT_RUNNING_WO" in result.stdout

def test_reconcile_detects_running_wo_without_worktree():
    result = subprocess.run(
        ["python", "scripts/ctx_reconcile_state.py", "--fixtures", "running_wo_without_worktree"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "RUNNING_WO_WITHOUT_WORKTREE" in result.stdout

def test_reconcile_apply_regenerates_lock_only_with_apply_flag():
    result = subprocess.run(
        ["python", "scripts/ctx_reconcile_state.py", "--fixtures", "running_without_lock"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "would_create_lock" in result.stdout

def test_reconcile_never_moves_states_without_force():
    result = subprocess.run(
        ["python", "scripts/ctx_reconcile_state.py", "--fixtures", "running_wo_without_worktree", "--apply"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "requires --force" in result.stdout

def test_reconcile_detects_duplicate_wo_id_across_states():
    result = subprocess.run(
        ["python", "scripts/ctx_reconcile_state.py", "--fixtures", "duplicate_wo_id_across_states"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "DUPLICATE_WO_ID" in result.stdout

def test_reconcile_detects_invalid_schema_and_refuses_apply():
    result = subprocess.run(
        ["python", "scripts/ctx_reconcile_state.py", "--fixtures", "invalid_schema"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "WO_INVALID_SCHEMA" in result.stdout

    result_apply = subprocess.run(
        ["python", "scripts/ctx_reconcile_state.py", "--fixtures", "invalid_schema", "--apply"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result_apply.returncode != 0
    assert "apply refused" in result_apply.stdout
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest -q tests/unit/test_ctx_reconcile_state.py`
Expected: FAIL because script does not exist.

**Step 3: Implement script**

Behavior:
- Read WOs from `_ctx/jobs/{pending,running,done,failed}/*.yaml`
- Read locks from `_ctx/jobs/running/*.lock`
- Read worktrees from `git worktree list` (or fixture `git_worktree_list.txt`)
- Validate WOs against schemas; report `WO_INVALID_SCHEMA`
- Report inconsistencies using the categories above
- `--apply` regenerates missing locks; `--force` required to move WO to `failed` with `x_reconcile_reason`
- `DUPLICATE_WO_ID` is severity `P0` and exits non-zero
- `WO_INVALID_SCHEMA` exits non-zero and refuses `--apply`
- If repo is clean and `--apply` is used, create a commit; otherwise write a patch file under `_ctx/logs/reconcile/`
- Write `_ctx/logs/reconcile/reconcile.log` with before/after when `--apply`
- `--json out.json` writes a machine-readable report
- JSON issues include: `code`, `severity`, `wo_id`, `paths`

**Step 4: Run test to verify it passes**

Run: `uv run pytest -q tests/unit/test_ctx_reconcile_state.py`
Expected: PASS.

**Step 5: Commit**

```bash
git add scripts/ctx_reconcile_state.py tests/fixtures/reconcile tests/unit/test_ctx_reconcile_state.py
git commit -m "feat: add reconcile state tool"
```

### Task 11: Implement ctx_wo_finish.py

**Files:**
- Create: `scripts/ctx_wo_finish.py`
- Test: `tests/unit/test_ctx_wo_finish.py`

**Step 1: Write the failing test**

```python
import subprocess

def test_wo_finish_help():
    result = subprocess.run([
        "python", "scripts/ctx_wo_finish.py", "--help"
    ], capture_output=True, text=True)
    assert result.returncode == 0
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest -q tests/unit/test_ctx_wo_finish.py`
Expected: FAIL because script does not exist.

**Step 3: Implement script**

Behavior:
- Validate DoD artifacts present in `_ctx/handoff/<WO>/`
- Update WO `result`, `finished_at`, `commit_sha`
- Move running -> done/failed

**Step 4: Run test to verify it passes**

Run: `uv run pytest -q tests/unit/test_ctx_wo_finish.py`
Expected: PASS.

**Step 5: Commit**

```bash
git add scripts/ctx_wo_finish.py tests/unit/test_ctx_wo_finish.py
git commit -m "feat: add wo finish script"
```

---

## Phase 4 - Monitoring and Iteration

**Deliverables**
- `scripts/ctx_status.py`
- `_ctx/metrics/wo_metrics.jsonl`
- `scripts/ctx_metrics_report.py`
- `docs/backlog/LESSONS.md`

**Acceptance Criteria**
- `ctx_status` runs in < 1s and flags stale WOs.
- Metrics append-only and reportable weekly.

**Metrics**
- Zero evidence failures after 2 iterations.
- Stable WO size distribution (<= 12 files, <= 400 LOC for 90% of WOs).

**Rollback**
- Stop running metrics scripts; no destructive changes required.

### Task 12: Implement ctx_status.py

**Files:**
- Create: `scripts/ctx_status.py`
- Test: `tests/unit/test_ctx_status.py`

**Step 1: Write the failing test**

```python
import subprocess

def test_ctx_status_help():
    result = subprocess.run(["python", "scripts/ctx_status.py", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest -q tests/unit/test_ctx_status.py`
Expected: FAIL because script does not exist.

**Step 3: Implement script**

Behavior:
- Summarize WOs by status
- Flag stale running WOs (> N days)

**Step 4: Run test to verify it passes**

Run: `uv run pytest -q tests/unit/test_ctx_status.py`
Expected: PASS.

**Step 5: Commit**

```bash
git add scripts/ctx_status.py tests/unit/test_ctx_status.py
git commit -m "feat: add ctx status report"
```

### Task 13: Implement metrics report

**Files:**
- Create: `scripts/ctx_metrics_report.py`
- Create: `_ctx/metrics/wo_metrics.jsonl`
- Test: `tests/unit/test_ctx_metrics_report.py`

**Step 1: Write the failing test**

```python
import subprocess

def test_ctx_metrics_help():
    result = subprocess.run(["python", "scripts/ctx_metrics_report.py", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest -q tests/unit/test_ctx_metrics_report.py`
Expected: FAIL because script does not exist.

**Step 3: Implement report**

Behavior:
- Append-only JSONL metrics
- Weekly summary output

**Step 4: Run test to verify it passes**

Run: `uv run pytest -q tests/unit/test_ctx_metrics_report.py`
Expected: PASS.

**Step 5: Commit**

```bash
git add scripts/ctx_metrics_report.py _ctx/metrics/wo_metrics.jsonl tests/unit/test_ctx_metrics_report.py
git commit -m "feat: add metrics reporting"
```

---

## Path Updates From Prior List (blacklog -> backlog)

- Moved: `docs/backlog/legacy/inputs/central_telefonica_v0.1.yaml` (from `_ctx/backlog/central_telefonica/central_telefonica_v0.1.yaml`)
- Created: `_ctx/jobs/pending/WO-0004.yaml`
- Created: `_ctx/jobs/pending/WO-0005.yaml`
- Created: `_ctx/blacklog/README.md`
- Created: `tests/integration/test_ctx_search_linter_ab_controlled.py`
- Created: `docs/reports/KNOWN_FAILS.md`
- Created: `_ctx/logs/ab_off.log`
- Created: `_ctx/logs/ab_on.log`
