# CI Baseline Remediation Branch-Review-First Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** clear the PR-level CI blocker that comes from baseline `mypy src/` failures while keeping the remediation PR auditable from the first commit through final `branch-review`.

**Architecture:** treat the CI cleanup as a separate remediation lot layered on top of `codex/wo-remediation-merge-ready`, with its own plan-backed review run and explicit artifact trail. Keep the lot narrow: first prove the baseline failure on `origin/main`, then fix the typed modules in small clusters, then run `branch-review` against this exact plan path, and finally delete the generated `review/...` branch after the run is closed.

**Tech Stack:** Git worktree workflow, GitHub Actions CI, `uv`, `ruff`, `mypy`, `reviewctl`, `gh`, Python 3.12/3.14 repo tooling.

### Task 1: Start The Lot With A Clean Branch-Review Contract

**Files:**
- Reference: `docs/plans/2026-03-14-ci-baseline-remediation-branch-review-first.md`
- Reference: `docs/plans/2026-03-14-remediation-anchor.md`
- Reference: `docs/reviewctl-agent-guide.md`
- Reference: `docs/reviewctl-quick-reference.md`
- Reference: `.reviewctl/project-gates.json`

**Step 1: Confirm the clean starting point**

Run:

```bash
git switch codex/wo-remediation-merge-ready
git status --short --branch
git fetch --prune origin
```

Expected: clean worktree on `codex/wo-remediation-merge-ready`.

**Step 2: Export the review environment in the same shell**

Run:

```bash
export REVIEW_API_TOKEN="${REVIEW_API_TOKEN:?missing REVIEW_API_TOKEN}"
export REVIEW_CLI="/Users/felipe_gonzalez/Developer/branch-review/mini-services/reviewctl/src/index.ts"
command -v bun
command -v jq
mkdir -p apps/pae-wizard/outputs/reviewctl
```

Expected: `bun`, `jq`, and `REVIEW_CLI` resolve successfully.

**Step 3: Verify the repo review surface before any code change**

Run:

```bash
test -f package.json && echo PACKAGE_JSON_OK
test -f biome.json && echo BIOME_CONFIG_OK
test -f pyproject.toml && echo RUFF_CONFIG_OK
jq -r '.scripts["lint:biome"] // "MISSING"' package.json
jq -r '.scripts["lint:ruff"] // "MISSING"' package.json
```

Expected: no missing static prerequisites.

### Task 2: Capture The CI Baseline As Evidence

**Files:**
- Create: `apps/pae-wizard/outputs/reviewctl/ci-baseline-main-mypy.md`
- Create: `apps/pae-wizard/outputs/reviewctl/ci-baseline-pr-mypy.md`
- Reference: `.github/workflows/ci.yml`

**Step 1: Reproduce the failing CI command on the PR branch**

Run:

```bash
uv run mypy src/ | tee apps/pae-wizard/outputs/reviewctl/ci-baseline-pr-mypy.md
```

Expected: the same family of `mypy` failures seen in GitHub Actions.

**Step 2: Reproduce the same command on `origin/main`**

Run:

```bash
tmpdir=$(mktemp -d /tmp/trifecta-main-ci-XXXXXX)
git worktree add --detach "$tmpdir" origin/main
(
  cd "$tmpdir"
  uv run mypy src/
) | tee apps/pae-wizard/outputs/reviewctl/ci-baseline-main-mypy.md
git worktree remove "$tmpdir" --force
```

Expected: baseline `mypy` failures also reproduce on `origin/main`.

**Step 3: Commit the evidence note if and only if the baseline is confirmed**

Update `docs/plans/2026-03-14-remediation-anchor.md` with:
- failing check name
- GitHub Actions run URL
- confirmation that `origin/main` reproduces the same `mypy` failure
- the artifact paths written above

### Task 3: Fix The PR-Scope Ruff Debt Without Broadening Scope Blindly

**Files:**
- Modify: `src/infrastructure/cli.py`
- Modify: `tests/integration/test_export_wo_index_atomicity.py`
- Modify: `tests/integration/test_path_canonicalization.py`
- Modify: `tests/integration/test_schema_version.py`
- Modify: `tests/unit/test_ctx_wo_gc.py`

**Step 1: Apply safe lint fixes only to the files that are true defects or duplicate registration**

Run:

```bash
uv run ruff check src/ tests/ --fix
uv run ruff format src/infrastructure/cli.py
```

Expected: only intentional CLI/test cleanup remains for manual inspection.

**Step 2: Manually fix the duplicate CLI registrations and unused test locals**

Implementation notes:
- keep the richer early `status` / `doctor` commands
- remove the later duplicate top-level `status` / `doctor` registrations
- keep top-level `repo-register` / `repo-list` / `repo-show` aliases, but give them unique Python function names
- remove unused locals from tests without weakening the assertions

**Step 3: Verify the lint-only slice**

Run:

```bash
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

Expected: both commands pass.

### Task 4: Burn Down The Baseline Mypy Failures In Small Clusters

**Files:**
- Modify: `src/trifecta/platform/runtime_manager.py`
- Modify: `src/trifecta/platform/registry.py`
- Modify: `src/platform/registry.py`
- Modify: `src/domain/segment_resolver.py`
- Modify: `src/application/zero_hit_reports.py`
- Modify: `src/domain/skill_contracts.py`
- Modify: `src/application/telemetry_health.py`
- Modify: `src/infrastructure/linear_mcp_client.py`
- Modify: `src/application/skill_lint_use_case.py`
- Modify: `src/application/linear_sync_use_case.py`
- Modify: `src/infrastructure/cli.py`

**Step 1: Fix import-path and wrapper return typing first**

Run:

```bash
uv run mypy src/trifecta/platform/runtime_manager.py src/trifecta/platform/registry.py src/platform/registry.py src/domain/segment_resolver.py
```

Expected: only these files are in play for the first cluster.

**Step 2: Fix collection typing and dict-shape issues second**

Run:

```bash
uv run mypy src/application/zero_hit_reports.py src/application/telemetry_health.py src/domain/skill_contracts.py
```

Expected: container annotations become concrete and iterable-safe.

**Step 3: Fix remaining infra/application typed API mismatches**

Run:

```bash
uv run mypy src/infrastructure/linear_mcp_client.py src/application/skill_lint_use_case.py src/application/linear_sync_use_case.py src/infrastructure/cli.py
```

Expected: argument/return mismatches are resolved.

**Step 4: Verify the full CI command**

Run:

```bash
uv run mypy src/
```

Expected: zero `mypy` errors.

### Task 5: Commit In Narrow, Reviewable Cuts

**Files:**
- Commit 1: lint-only cleanup
- Commit 2+: one typed cluster per commit
- Final doc commit: anchor + evidence updates

**Step 1: Commit the lint-only slice**

Run:

```bash
git add src/infrastructure/cli.py tests/integration/test_export_wo_index_atomicity.py tests/integration/test_path_canonicalization.py tests/integration/test_schema_version.py tests/unit/test_ctx_wo_gc.py
git commit -m "fix(ci): clear ruff blockers in cli and tests"
```

**Step 2: Commit each `mypy` cluster separately**

Run pattern:

```bash
git add <exact files for one cluster>
git commit -m "fix(types): <cluster summary>"
```

Expected: no omnibus commit.

### Task 6: Run Plan-Backed Branch Review For This Lot

**Files:**
- Reference: `docs/plans/2026-03-14-ci-baseline-remediation-branch-review-first.md`
- Output: `_ctx/review_runs/run_*/`
- Output: `apps/pae-wizard/outputs/reviewctl/`

**Step 1: Start the canonical flow with the explicit plan path**

Run:

```bash
bun "$REVIEW_CLI" init --create
bun "$REVIEW_CLI" explore context
bun "$REVIEW_CLI" explore diff
bun "$REVIEW_CLI" plan --plan-path docs/plans/2026-03-14-ci-baseline-remediation-branch-review-first.md
bun "$REVIEW_CLI" run
```

Expected: `plan_status` is `FOUND` or `AUTOGENERATED`, not an implicit plan-less run.

**Step 2: Verify the run contract and required agents**

Run:

```bash
RUN_ID=$(ls -1dt _ctx/review_runs/run_* | head -n 1 | xargs basename)
test -f "_ctx/review_runs/${RUN_ID}/plan.json" && echo PLAN_JSON_OK
jq -r '.plan_status // "MISSING"' "_ctx/review_runs/${RUN_ID}/plan.json"
jq -r '.required_agents[]?' "_ctx/review_runs/${RUN_ID}/plan.json"
```

Expected: required agents are explicit before ingest/verdict.

**Step 3: Re-run conclusive statics and verdict**

Run:

```bash
bun run lint:biome > /tmp/biome-output.md 2>&1
bun run lint:ruff > /tmp/ruff-output.md 2>&1
uv run mypy src/ > /tmp/mypy-output.md 2>&1
bun "$REVIEW_CLI" ingest --static biome --input /tmp/biome-output.md
bun "$REVIEW_CLI" ingest --static ruff --input /tmp/ruff-output.md
bun "$REVIEW_CLI" verdict
```

Expected: final verdict reaches `PASS` or a conclusive `FAIL`, never `INCOMPLETE`.

### Task 7: Close The Lot Cleanly, Including Review Branch Cleanup

**Files:**
- Modify: `docs/plans/2026-03-14-remediation-anchor.md`

**Step 1: Record the final CI and branch-review result in the anchor**

Capture:
- check URLs
- final `RUN_ID`
- final verdict from `_ctx/review_runs/<run-id>/final.json`
- whether the review stayed plan-backed
- debt log paths

**Step 2: Push the branch and verify the PR head**

Run:

```bash
git push
gh pr view 71 --json url,headRefOid,statusCheckRollup
```

**Step 3: Delete the generated local review branch after the run is closed**

Run:

```bash
git branch --list 'review/*'
git branch -D "$(git branch --list 'review/main--codex_wo-remediation-merge-ready--*' | sed 's/^..//')"
```

Expected: no stale local `review/...` branch remains after reporting the result.
