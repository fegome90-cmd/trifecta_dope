# Main CI Stabilization and WO Merge Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Stabilize `main` CI/security pipelines first, then rebase and merge WO hygiene changes safely.

**Architecture:** Two-track remediation. Track A fixes repository-level workflow breakages (`Secret Scanning`, `CodeQL`, `Codecov`) that fail independently of feature code. Track B fixes deterministic lint/test regressions in `main` and only then integrates WO hygiene branch to avoid mixed-cause failures.

**Tech Stack:** Python 3.12+, pytest, ruff, GitHub Actions (`.github/workflows/*.yml`), gh CLI.

### Task 1: Create isolated stabilization branch from main

**Files:**
- Modify: none (git operation only)
- Test: none

**Step 1: Create clean worktree**

Run:
```bash
git fetch origin main
git worktree add .worktrees/ci-main-unblock -b codex/ci-main-unblock origin/main
```

**Step 2: Verify baseline branch state**

Run:
```bash
git -C .worktrees/ci-main-unblock status --short --branch
```

Expected: clean worktree on `codex/ci-main-unblock`.

### Task 2: Fix CI workflow blockers that are not code regressions

**Files:**
- Modify: `.github/workflows/security-scan.yml`
- Modify: `.github/workflows/ci.yml`
- Test: workflow dry checks via local syntax/lint + `gh` rerun after push

**Step 1: Patch Secret Scanning push logic**

Goal: prevent `base=main`/`head=HEAD` same-commit failure on push builds.

**Step 2: Patch CodeQL upload behavior**

Goal: avoid hard failure when repository lacks code scanning feature (graceful skip or conditional execution).

**Step 3: Patch Codecov token handling**

Goal: prevent hard fail on protected/non-tokenless contexts (set `fail_ci_if_error: false` or conditional token strategy).

**Step 4: Validate YAML and CI workflow syntax**

Run:
```bash
uv run python -m compileall .github/workflows || true
```

Expected: no malformed YAML edits (actual GH validation on push).

**Step 5: Commit**

```bash
git -C .worktrees/ci-main-unblock add .github/workflows/security-scan.yml .github/workflows/ci.yml
git -C .worktrees/ci-main-unblock commit -m "ci: make security and coverage workflows fail-safe on main"
```

### Task 3: Fix deterministic lint failures on main

**Files:**
- Modify: `src/cli/introspection.py`
- Modify: `src/cli/invalid_option_handler.py`
- Modify: `src/domain/wo_transactions.py`
- Modify: `tests/integration/test_cli_flag_snapshots.py`
- Modify: `tests/integration/test_transaction_recovery.py`
- Modify: `tests/integration/test_wo_closure.py`
- Modify: `tests/test_wo_orchestration.py`
- Modify: `tests/unit/test_ctx_reconcile_state.py`
- Modify: `tests/unit/test_helpers_lock_concurrent.py`
- Modify: `tests/unit/test_metadata_inference.py`
- Modify: `tests/unit/test_telemetry_rotate.py`
- Modify: `tests/unit/test_wo_business_logic.py`
- Modify: `tests/unit/test_wo_finish_cli.py`
- Modify: `tests/unit/test_wo_finish_validators.py`

**Step 1: Auto-fix safe Ruff issues**

Run:
```bash
uv run ruff check src/ tests/ --fix
```

**Step 2: Manually resolve residual Ruff issues**

Focus: E402/F841 leftovers in `tests/test_wo_orchestration.py` and `tests/unit/test_telemetry_rotate.py`.

**Step 3: Verify lint clean**

Run:
```bash
uv run ruff check src/ tests/
```

Expected: `All checks passed`.

**Step 4: Commit**

```bash
git -C .worktrees/ci-main-unblock add src tests
git -C .worktrees/ci-main-unblock commit -m "test: resolve repository-wide ruff violations"
```

### Task 4: Fix failing unit/integration tests in main baseline

**Files:**
- Modify: `tests/unit/test_ctx_pending_wos.py`
- Modify: `tests/unit/test_ctx_schemas.py`
- Modify: `docs/backlog/schema/backlog.schema.json`
- Modify: `tests/unit/test_telemetry_rotate.py`
- Modify: `tests/integration/test_ctx_pipeline_real_wo.py`
- Modify: `scripts/helpers.py` (if rollback patching point is wrong)
- Modify: `tests/integration/test_transaction_recovery.py`
- Create/Modify fixture path: `tests/fixtures/closure/wo_no_handoff/**`
- Modify: `tests/integration/test_wo_closure.py`

**Step 1: Write/adjust failing expectations for pending WOs**

Update hardcoded WO existence checks to align with canonical current backlog state.

**Step 2: Fix backlog schema compatibility**

Either:
- include root `generated_at` in `_ctx/backlog/backlog.yaml`, or
- relax schema/tests consistently.

Recommended: keep schema strict and make backlog/test aligned.

**Step 3: Fix date-fragile telemetry rotate test**

Replace hardcoded date `20260210` with regex/format assertion.

**Step 4: Fix WO take integration cwd/root behavior**

Ensure subprocessed git worktree commands run with repo root `cwd` and not fixture root.

**Step 5: Fix rollback failure simulation test**

Patch target where function is actually referenced (module-local import path), not origin module only.

**Step 6: Add missing closure fixture or update test to existing fixture**

Ensure `tests/fixtures/closure/wo_no_handoff` exists and matches test contract.

**Step 7: Verify focused tests**

Run:
```bash
uv run pytest -q tests/unit/test_ctx_pending_wos.py
uv run pytest -q tests/unit/test_ctx_schemas.py
uv run pytest -q tests/unit/test_telemetry_rotate.py
uv run pytest -q tests/integration/test_ctx_pipeline_real_wo.py::test_real_wo_validates_and_can_be_taken
uv run pytest -q tests/integration/test_transaction_recovery.py::TestTransactionRecoveryScenarios::test_rollback_with_multiple_failures
uv run pytest -q tests/integration/test_wo_closure.py::TestWoClosureWithFixtures::test_validate_dod_missing_directory
```

**Step 8: Commit**

```bash
git -C .worktrees/ci-main-unblock add tests scripts docs/backlog/schema
git -C .worktrees/ci-main-unblock commit -m "test: stabilize wo and telemetry baseline tests on main"
```

### Task 5: Full local gate before opening stabilization PR

**Files:**
- Modify: none
- Test: full local verification

**Step 1: Run required checks**

```bash
uv run ruff check src/ tests/
uv run pytest tests/unit -q
uv run pytest tests/integration -q
```

**Step 2: Optional parity with CI command set**

```bash
uv run pytest --cov=src --cov-report=xml tests/unit tests/integration tests/acceptance -q
```

**Step 3: Push and open PR**

```bash
git -C .worktrees/ci-main-unblock push -u origin codex/ci-main-unblock
gh pr create --base main --head codex/ci-main-unblock --title "ci: unblock main pipeline and baseline tests" --body-file /tmp/pr_ci_unblock.md
```

### Task 6: Rebase WO hygiene branch after main stabilization merges

**Files:**
- Modify: branch history only
- Test: WO-specific gates

**Step 1: Sync and rebase**

```bash
git fetch origin
git checkout codex/chore-wo-hygiene
git rebase origin/main
```

**Step 2: Re-run WO gates**

```bash
make wo-fmt-check
make wo-lint
make wo-lint-json
```

Expected: 0 findings.

**Step 3: Resolve any drift from main fixes and push**

```bash
git push --force-with-lease
```

### Task 7: Final merge readiness and audit trail

**Files:**
- Modify: `docs/evidence/wo-hygiene-PR25.md` (if needed)
- Modify: PR descriptions

**Step 1: Confirm PR #25 checks are green after rebase**

Run:
```bash
gh pr view 25 --json statusCheckRollup,mergeable,url
```

**Step 2: Confirm evidence document reflects final SHAs**

Include:
- stabilization PR SHA
- rebased WO hygiene SHA
- latest `make wo-lint` and `make wo-fmt-check` output

**Step 3: Merge PR #25**

Use merge method aligned with repo policy.

---

## Risk Controls

1. Do not touch user’s dirty workspace; all changes in isolated worktree.
2. Keep workflow fixes and test/code fixes in separate commits.
3. Verify after each task (no “done” claim without fresh command output).
4. Rebase WO branch only after main stabilization merge to reduce conflict churn.
