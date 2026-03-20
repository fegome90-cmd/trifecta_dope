# Non-Graph CI Remediation Sprint Plan

> **For Codex:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task.
> **Workflow rule:** Run `skill-hub "<current task instruction>"` before every sprint phase and before every new concrete task inside a phase.

**Goal:** Stabilize non-Graph CI debt without contaminating Graph PR scope, then flow the stabilization back into `codex/graph-mvp` only through a clean `main` merge.

**Architecture:** Treat this as a manual sprint that mimics WO discipline without WO state machinery. Use one integration branch rooted at `main`, one isolated worktree per sprint slice, strict slice-by-slice verification, and frequent noise checks so unrelated churn does not leak into the sprint.

**Tech Stack:** `git worktree`, `uv`, `pytest`, `ruff`, GitHub PR checks, local session logging in `_ctx/session_trifecta_dope.md`

---

## Sprint Operating Rules

- Do not implement non-Graph remediation on `codex/graph-mvp`.
- Do not merge remediation branches into `codex/graph-mvp` directly.
- Root the sprint on fresh `main`.
- Use one branch and one isolated worktree per sprint slice.
- Finish each slice end-to-end before starting the next slice.
- Before each slice: run `skill-hub` for that exact slice objective.
- Before each commit claim: run only the narrowest relevant gates first, then the broader slice gate.
- After each slice merge: review noise with `git status --short --branch`, `git diff --stat`, and the relevant test/lint gate.
- If a slice uncovers unrelated debt, log it and stop scope creep unless it blocks the current slice gate.

## Sprint Gate Semantics

**Slice green** means:

- the active slice branch passes its targeted gate set
- the slice does not regress already-completed slices
- the slice worktree is clean enough to merge into the sprint anchor

**Sprint green** means:

- the sprint anchor passes `uv run ruff check .`
- the sprint anchor passes `uv run pyrefly check`
- the sprint anchor passes the full intended integration gate

**Rule:** early slices only need to become `slice green`. The sprint anchor is allowed to be partially complete until the prerequisite slices are merged. Claim `sprint green` only at final verification.

## Branch And Worktree Topology

### Sprint Anchor

**Branch:** `codex/non-graph-ci-sprint`

**Worktree:** `.worktrees/codex-non-graph-ci-sprint`

**Purpose:** Integration anchor for the sprint. No feature work happens here first. This branch only receives verified slice merges.

### Slice Branch Pattern

- Branch naming: `codex/sprint-ci-<slice>`
- Worktree naming: `.worktrees/codex-sprint-ci-<slice>`
- Merge target: `codex/non-graph-ci-sprint`
- Final merge target after full sprint verification: `main`

### Recommended Slice Names

- `codex/sprint-ci-ruff-hygiene`
- `codex/sprint-ci-cli-flag-snapshots`
- `codex/sprint-ci-integration-contracts-a`
- `codex/sprint-ci-integration-contracts-b`
- `codex/sprint-ci-macos-portability` only if still needed after Linux CI is green

## Manual Sprint Lifecycle

Each slice follows this exact lifecycle:

1. Create branch from current sprint anchor.
2. Create isolated worktree for that branch.
3. Capture baseline noise for that slice.
4. Implement only the scoped fix set.
5. Run narrow tests first.
6. Run slice-level lint/type/test gate.
7. Self-review with `git diff --stat` and targeted file review.
8. Merge slice back into `codex/non-graph-ci-sprint`.
9. Re-run sprint anchor verification before opening the next slice.
10. Remove the slice worktree with `git worktree remove`.

## Sprint 0: Anchor Setup And Baseline

**Files to inspect:**
- `tests/integration/test_cli_flag_snapshots.py`
- `tests/integration/test_export_wo_index_atomicity.py`
- `tests/integration/test_lsp_contract_fallback.py`
- `tests/integration/test_skill_lint_cli.py`
- `tests/integration/test_wo_crash_safety.py`
- `tests/integration/test_wo_take_concurrency.py`
- `scripts/wo_verify.sh`

**Step 1: Refresh main and create sprint anchor idempotently**

Run:

```bash
git checkout main
git pull --ff-only
git check-ignore .worktrees
git branch --list codex/non-graph-ci-sprint
git worktree list
```

**Decision rules:**

- If `git check-ignore .worktrees` does not report `.worktrees`, stop and fix the ignore rule before creating any sprint worktree.
- If `codex/non-graph-ci-sprint` does not exist, create it from fresh `main`.
- If the branch exists and is already attached to the expected worktree, reuse it.
- If the branch exists but the worktree path is stale, remove the stale worktree with `git worktree remove` or `git worktree prune` before recreating it.

Then create or reuse the anchor:

```bash
git branch codex/non-graph-ci-sprint
git worktree add .worktrees/codex-non-graph-ci-sprint codex/non-graph-ci-sprint
```

**Step 2: Capture baseline evidence from the sprint anchor**

Run:

```bash
cd .worktrees/codex-non-graph-ci-sprint
uv run ruff check .
uv run pytest -q tests/integration -x
```

**Expected outcome:** current blocker list is reproducible from the anchor and remains clearly outside Graph scope.

**Step 3: Record baseline noise**

Run:

```bash
git status --short --branch
git diff --stat main...HEAD
git worktree list
```

**Expected outcome:** anchor starts clean and any pre-existing repo noise is visible before slice work begins.

## Sprint 1: Ruff Hygiene Sweep

**Files:**
- `eval/scripts/`
- `scripts/`
- `tests/`

**Goal:** eliminate the current cross-surface Ruff debt so CI lint is no longer failing on obvious hygiene noise.

**Execution notes:**
- Group fixes by subsystem, not by random file order.
- Prefer safe mechanical fixes first: unused imports, unnecessary f-strings, bare except cleanup when trivial.
- If a finding needs behavior change, defer it to the relevant later slice unless it blocks `ruff`.

**Primary gate:**

```bash
uv run ruff check .
```

**Anchor gate after merge:**

```bash
git diff --stat main...HEAD
uv run ruff check .
```

## Sprint 2: CLI Snapshot Contract

**Files:**
- `tests/integration/test_cli_flag_snapshots.py`
- CLI registration surface if snapshot drift is intentional

**Goal:** resolve the `trifecta ctx search` flag contract drift cleanly.

**Decision rule:**
- If `--explain` and `--explain-format` are intentional product surface, update the snapshots and add a note in the slice commit message.
- If they are accidental exposure, remove them from the runtime surface and keep the snapshots stable.

**Primary gate:**

```bash
uv run pytest -q tests/integration/test_cli_flag_snapshots.py
```

**Secondary gate:**

```bash
uv run pytest -q tests/integration/test_cli_flag_snapshots.py
```

## Sprint 3: Integration Contracts A

**Files:**
- `tests/integration/test_export_wo_index_atomicity.py`
- `tests/integration/test_lsp_contract_fallback.py`
- `tests/integration/test_skill_lint_cli.py`

**Goal:** clear the next contract-style integration failures after snapshot drift is resolved.

**Execution notes:**
- Keep export/index atomicity isolated from LSP fallback work unless the same root cause is proven.
- Treat `skill lint` failures as CLI contract work, not docs work, unless evidence says otherwise.

**Primary gate:**

```bash
uv run pytest -q \
  tests/integration/test_export_wo_index_atomicity.py \
  tests/integration/test_lsp_contract_fallback.py \
  tests/integration/test_skill_lint_cli.py
```

**Secondary gate:**

```bash
uv run pytest -q \
  tests/integration/test_cli_flag_snapshots.py \
  tests/integration/test_export_wo_index_atomicity.py \
  tests/integration/test_lsp_contract_fallback.py \
  tests/integration/test_skill_lint_cli.py
```

## Sprint 4: Integration Contracts B

**Files:**
- `tests/integration/test_wo_crash_safety.py`
- `tests/integration/test_wo_take_concurrency.py`

**Goal:** clear the remaining concurrency and crash-safety integration failures without enabling WO lifecycle usage.

**Execution notes:**
- Preserve the current "WO blocked" operating constraint.
- Fix contracts and safety checks without requiring the team to adopt WO commands during the sprint.

**Primary gate:**

```bash
uv run pytest -q \
  tests/integration/test_wo_crash_safety.py \
  tests/integration/test_wo_take_concurrency.py
```

**Secondary gate:**

```bash
uv run pytest -q \
  tests/integration/test_cli_flag_snapshots.py \
  tests/integration/test_export_wo_index_atomicity.py \
  tests/integration/test_lsp_contract_fallback.py \
  tests/integration/test_skill_lint_cli.py \
  tests/integration/test_wo_crash_safety.py \
  tests/integration/test_wo_take_concurrency.py
```

## Sprint 5: Optional macOS Portability Slice

**File:**
- `scripts/wo_verify.sh`

**Goal:** fix the local macOS `date -d` portability bug only after Linux CI blockers are already controlled.

**Rule:** do not let this slice block the Linux CI stabilization sprint.

**Primary gate:**

```bash
bash scripts/wo_verify.sh
```

**Caveat:** if this script requires repo state setup, document the exact repro and keep the fix isolated from Linux-only CI closure.

## Final Sprint Verification

From `.worktrees/codex-non-graph-ci-sprint` run:

```bash
uv run ruff check .
uv run pyrefly check
uv run pytest -q tests/integration
uv run pytest -q tests/integration -x
git status --short --branch
git diff --stat main...HEAD
```

## Clean Merge Strategy

1. Merge each verified slice branch into `codex/non-graph-ci-sprint`.
2. Keep the anchor at the expected cumulative state after every slice merge.
3. When the sprint anchor is green, open or merge that anchor into `main`.
4. Only after `main` contains the sprint fixes, update `codex/graph-mvp` with:

```bash
git checkout codex/graph-mvp
git merge origin/main
```

5. Re-run the focused Graph slice after the merge from `main`.

## Constant Noise Checks

Run these before and after every slice:

```bash
git status --short --branch
git diff --stat
git worktree list
```

Run these after every slice merge into the sprint anchor:

```bash
git diff --stat main...HEAD
```

Run the cumulative gate that matches the completed slices:

```bash
# After Sprint 1
uv run ruff check .

# After Sprint 2
uv run ruff check .
uv run pytest -q tests/integration/test_cli_flag_snapshots.py

# After Sprint 3
uv run ruff check .
uv run pytest -q \
  tests/integration/test_cli_flag_snapshots.py \
  tests/integration/test_export_wo_index_atomicity.py \
  tests/integration/test_lsp_contract_fallback.py \
  tests/integration/test_skill_lint_cli.py

# After Sprint 4 and before merge to main
uv run ruff check .
uv run pyrefly check
uv run pytest -q tests/integration
```

If a command reveals unrelated churn, stop and decide explicitly whether it is:

- required blocker work for the active slice
- deferable debt to log outside the sprint
- evidence that the slice boundary is wrong and needs replanning

## Definition Of Done

- `codex/graph-mvp` remained untouched for non-Graph remediation work.
- Non-Graph remediation happened only in isolated sprint worktrees.
- Sprint anchor is `sprint green` against the agreed gates.
- `main` receives the remediation before `codex/graph-mvp` is refreshed.
- Graph verification is rerun only after the clean `main` merge.
- Session log and handoff artifacts reflect the final state.

## First Execution Prompt

When execution starts, the first task is:

```bash
skill-hub "set up an isolated sprint anchor branch and worktree for non-Graph CI remediation"
```
