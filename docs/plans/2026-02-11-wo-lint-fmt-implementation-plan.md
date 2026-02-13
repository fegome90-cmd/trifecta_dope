# WO Lint + Formatter Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implementar un linter y formatter de Work Orders que validen y normalicen todos los WO YAML bajo `_ctx/jobs/**`, compatibles con los scripts actuales (`ctx_wo_take.py`, `ctx_backlog_validate.py`).

**Architecture:** Se crearán dos CLIs Python en `scripts/`: `ctx_wo_lint.py` (validación schema + semántica) y `ctx_wo_fmt.py` (normalización de formato/orden). Ambos compartirán descubrimiento de archivos WO por estado (`pending/running/done/failed`), excluirán rutas `legacy`, y tendrán modo check/fix para CI y pre-commit.

**Tech Stack:** Python 3.12+, `PyYAML`, `jsonschema`, `pytest`, `uv`, Makefile, pre-commit.

### Task 1: Contract Baseline (Red)

**Files:**
- Create: `tests/unit/test_ctx_wo_lint_contract.py`
- Read-only reference: `scripts/ctx_backlog_validate.py`
- Read-only reference: `docs/backlog/schema/work_order.schema.json`
- Read-only reference: `docs/backlog/schema/backlog.schema.json`

**Step 1: Write failing tests for contract discovery**

```python
def test_lint_discovers_all_wo_yaml_states():
    ...

def test_lint_excludes_legacy_paths():
    ...

def test_lint_accepts_current_wo_id_patterns():
    ...
```

**Step 2: Run tests to verify failure**

Run: `uv run pytest tests/unit/test_ctx_wo_lint_contract.py -v`
Expected: FAIL (script/module not found or assertions fail).

**Step 3: Create minimal placeholders for future modules**

Create stubs:
- `scripts/ctx_wo_lint.py`
- `scripts/ctx_wo_fmt.py`

**Step 4: Re-run tests**

Run: `uv run pytest tests/unit/test_ctx_wo_lint_contract.py -v`
Expected: still FAIL but now imports resolve.

**Step 5: Commit**

```bash
git add tests/unit/test_ctx_wo_lint_contract.py scripts/ctx_wo_lint.py scripts/ctx_wo_fmt.py
git commit -m "test(wo): add contract baseline for wo lint/fmt"
```

### Task 2: Linter Core (Green)

**Files:**
- Modify: `scripts/ctx_wo_lint.py`
- Modify: `tests/unit/test_ctx_wo_lint_contract.py`
- Create: `tests/unit/test_ctx_wo_lint_semantics.py`

**Step 1: Write failing semantic tests**

```python
def test_lint_flags_yaml_parse_errors(): ...
def test_lint_flags_missing_scope_allow_deny(): ...
def test_lint_flags_missing_verify_commands(): ...
def test_lint_validates_epic_and_dod_references(): ...
def test_lint_json_output_shape(): ...
```

**Step 2: Run tests to verify failure**

Run: `uv run pytest tests/unit/test_ctx_wo_lint_semantics.py -v`
Expected: FAIL.

**Step 3: Implement minimal linter behavior**

Implement in `scripts/ctx_wo_lint.py`:
- discovery: `_ctx/jobs/{pending,running,done,failed}/WO-*.yaml`
- schema validation against `docs/backlog/schema/work_order.schema.json`
- semantic checks:
  - `id` equals filename stem
  - status matches state folder
  - `epic_id` exists in `_ctx/backlog/backlog.yaml`
  - `dod_id` exists in `_ctx/dod/*.yaml`
  - `scope.allow` and `scope.deny` present
  - `verify.commands` required for `pending/running` (configurable)
- flags: `--json`, `--strict`, `--root`
- exit codes: `0` ok, `1` errors.

**Step 4: Run tests to verify pass**

Run: `uv run pytest tests/unit/test_ctx_wo_lint_contract.py tests/unit/test_ctx_wo_lint_semantics.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add scripts/ctx_wo_lint.py tests/unit/test_ctx_wo_lint_contract.py tests/unit/test_ctx_wo_lint_semantics.py
git commit -m "feat(wo): implement wo linter with schema and semantic checks"
```

### Task 3: Formatter (Green)

**Files:**
- Modify: `scripts/ctx_wo_fmt.py`
- Create: `tests/unit/test_ctx_wo_fmt.py`

**Step 1: Write failing formatter tests**

```python
def test_fmt_check_detects_unformatted_file(): ...
def test_fmt_write_reorders_top_level_keys(): ...
def test_fmt_preserves_valid_yaml_semantics(): ...
```

**Step 2: Run tests to verify failure**

Run: `uv run pytest tests/unit/test_ctx_wo_fmt.py -v`
Expected: FAIL.

**Step 3: Implement minimal formatter**

Implement in `scripts/ctx_wo_fmt.py`:
- same WO file discovery as linter
- flags: `--check` and `--write` (mutually exclusive)
- canonical top-level key order:
  - `version,id,epic_id,title,priority,status,owner,branch,worktree,scope,verify,dod_id,dependencies`
- stable YAML output (`sort_keys=False`, newline final).

**Step 4: Run tests to verify pass**

Run: `uv run pytest tests/unit/test_ctx_wo_fmt.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add scripts/ctx_wo_fmt.py tests/unit/test_ctx_wo_fmt.py
git commit -m "feat(wo): add wo formatter with check/write modes"
```

### Task 4: Tooling Integration

**Files:**
- Modify: `Makefile`
- Modify: `.pre-commit-config.yaml` (if present)
- Modify: `docs/backlog/OPERATIONS.md`

**Step 1: Add failing integration tests/document checks**

```python
def test_makefile_includes_wo_targets(): ...
```

**Step 2: Run tests to verify failure**

Run: `uv run pytest tests/unit/test_ctx_backlog_layout.py -v`
Expected: FAIL for missing targets/docs references.

**Step 3: Add targets and hooks**

Add Make targets:
- `wo-lint`
- `wo-lint-json`
- `wo-fmt`
- `wo-fmt-check`

Add pre-commit hooks for lint/fmt check.

**Step 4: Run verification**

Run:
- `uv run python scripts/ctx_wo_lint.py --strict`
- `uv run python scripts/ctx_wo_fmt.py --check`

Expected: exit codes align with repo state.

**Step 5: Commit**

```bash
git add Makefile .pre-commit-config.yaml docs/backlog/OPERATIONS.md
git commit -m "chore(wo): integrate wo lint/fmt in make and pre-commit"
```

### Task 5: Final Verification and Hardening

**Files:**
- Modify (if needed): `scripts/ctx_backlog_validate.py`
- Modify (if needed): `tests/unit/test_ctx_backlog_validate.py`

**Step 1: Run full relevant test suite**

Run:
- `uv run pytest tests/unit/test_ctx_wo_take.py -v`
- `uv run pytest tests/unit/test_ctx_backlog_validate.py -v`
- `uv run pytest tests/unit/test_ctx_wo_lint_contract.py tests/unit/test_ctx_wo_lint_semantics.py tests/unit/test_ctx_wo_fmt.py -v`

Expected: PASS.

**Step 2: Run operational commands**

Run:
- `uv run python scripts/ctx_wo_take.py --list`
- `uv run python scripts/ctx_wo_take.py --status`
- `uv run python scripts/ctx_backlog_validate.py --strict`

Expected: commands execute deterministically; strict validation behavior documented.

**Step 3: Reconcile strictness policy**

If `ctx_backlog_validate --strict` fails by legacy/minimal WOs, decide one policy and implement:
- A) enforce full schema for all WO files (migrate all files), or
- B) allow profile-based validation by state/version with explicit warnings.

**Step 4: Update docs and session evidence**

- append summary to `_ctx/session_trifecta_dope.md` using established protocol.
- document policy in `docs/backlog/WORKFLOW.md`.

**Step 5: Commit**

```bash
git add scripts/ctx_backlog_validate.py tests/unit/test_ctx_backlog_validate.py docs/backlog/WORKFLOW.md _ctx/session_trifecta_dope.md
git commit -m "refactor(wo): align strict validation policy with wo lint/fmt"
```
