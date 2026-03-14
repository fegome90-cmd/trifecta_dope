# Remediation Anchor

Date: 2026-03-14
Purpose: preserve the remediation thread across branch switches, worktree changes, and future merge/PR work without reopening already-classified surfaces.

## Canonical State

- Current clean merge candidate branch: `codex/wo-remediation-merge-ready`
- Current clean merge candidate HEAD: `8c2de43`
- Base of clean merge candidate: `origin/main` at `fca52dc`
- Original long-lived remediation branch: `codex/wo-remediation-plan`
- Original long-lived remediation HEAD: `f49ef95`
- Preserved non-mergeable local artifacts: `stash@{0}` named `remediation-nonmerge-artifacts`

## What Was Recovered

- The original remediation worktree was classified into mergeable versus non-mergeable artifacts.
- The non-mergeable local artifacts were preserved in `stash@{0}` instead of being mixed into the merge candidate.
- Two authoritative remediation commits were isolated on the long-lived branch:
  - `64e750f` `chore(remediation): [emergency] snapshot wo-0061 and wo-0067 state`
  - `f49ef95` `docs(remediation): [bypass] harden e-0020 execution contract`
- Those two commits were then replayed onto a fresh branch from `origin/main` as:
  - `17cce3c` `chore(remediation): [emergency] snapshot wo-0061 and wo-0067 state`
  - `8c2de43` `docs(remediation): [bypass] harden e-0020 execution contract`
- The clean PR surface was reduced from the long-lived branch delta to a 2-commit branch ahead of `origin/main`.
- Verification run on the clean branch:
  - `uv run python scripts/ctx_backlog_validate.py --strict`

## What Is In Scope On The Clean Branch

- `_ctx/backlog/backlog.yaml`
- `_ctx/jobs/done/WO-0061.yaml`
- `_ctx/jobs/done/WO-0067.yaml`
- `_ctx/jobs/pending/WO-0062.yaml`
- `_ctx/jobs/pending/WO-0063.yaml`
- `_ctx/jobs/pending/WO-0064.yaml`
- `_ctx/jobs/pending/WO-0065.yaml`
- `_ctx/jobs/pending/WO-0066.yaml`
- `docs/plans/2026-03-09-wo-remediation-execution-decomposition.md`

## What Was Explicitly Kept Out Of The Merge Candidate

- Checkpoints and handoff artifacts created during the merge review window
- Session log noise
- Telemetry and index noise
- The checkpoint-resume planning artifact
- `src/application/wo_authority.py` brought laterally
- The orphan test mentioned in the prior handoff

These artifacts were intentionally separated because they were not part of the safe mergeable lot.

## Pending Decisions

- Decide whether to push `codex/wo-remediation-merge-ready` and open a PR from that branch.
- Decide whether to merge locally after reconciling how `main` local differs from `origin/main`.
- Decide whether `stash@{0}` should remain preserved only or be reviewed in a separate follow-up task.
- Decide whether to create a second cleanup track for the non-mergeable artifacts instead of reopening this merge candidate.

## Active Blockers

- `branch-review` and `reviewctl` were not run successfully.
- Missing prerequisites called out in the prior handoff:
  - `REVIEW_API_TOKEN`
  - `package.json`
  - `docs/reviewctl-agent-guide.md`
  - `docs/reviewctl-quick-reference.md`
  - `apps/pae-wizard/outputs/reviewctl`

## Guardrails

- Do not open a PR from `codex/wo-remediation-plan`; it is a long-lived branch and will over-include unrelated history.
- Do not restore `stash@{0}` into `codex/wo-remediation-merge-ready` by accident.
- Do not claim `branch-review` passed; preflight was blocked and `reviewctl` did not run.
- Remember that the two remediation commits used audited bypasses for hook blockers. Treat that as recorded historical fact, not as permission to broaden manual state edits.

## Documents To Read First

Read these first regardless of branch:

1. `_ctx/handoff/remediation-merge-review-next-window.md`
2. `_ctx/handoff/remediation-merge-review-next-window-checklist.md`
3. `docs/plans/2026-03-14-remediation-anchor.md`
4. `docs/plans/2026-03-09-wo-remediation-execution-decomposition.md`

## Secondary Documents Still Relevant

These remain part of the remediation narrative, but some live only on `codex/wo-remediation-plan` rather than the clean merge branch:

- `docs/plans/2026-03-09-wo-remediation-plan.md`
- `docs/plans/2026-03-09-wo-remediation-plan-iteration-2.md`
- `docs/research/2026-03-09-wo-contrast-corrected.md`
- `docs/research/2026-03-09-wo-forensics-cloop.md`
- `docs/research/2026-03-09-wo-forensics-prevalence-severity.md`

If those files are not present on the current branch, read them with:

```bash
git show codex/wo-remediation-plan:docs/plans/2026-03-09-wo-remediation-plan.md
git show codex/wo-remediation-plan:docs/plans/2026-03-09-wo-remediation-plan-iteration-2.md
git show codex/wo-remediation-plan:docs/research/2026-03-09-wo-contrast-corrected.md
git show codex/wo-remediation-plan:docs/research/2026-03-09-wo-forensics-cloop.md
git show codex/wo-remediation-plan:docs/research/2026-03-09-wo-forensics-prevalence-severity.md
```

## Fast Reorientation Commands

```bash
git switch codex/wo-remediation-merge-ready
git status --short --branch
git log --oneline origin/main..HEAD
git diff --stat origin/main...HEAD
git stash list | sed -n '1,3p'
git stash show --stat stash@{0}
```

## Exit Criteria For This Thread

This thread is directionally complete only when one of these happens:

- `codex/wo-remediation-merge-ready` is pushed and used as the PR branch, or
- the same clean 2-commit surface is merged locally in a controlled way, or
- the remaining work is explicitly split into a new task for non-mergeable artifacts.
