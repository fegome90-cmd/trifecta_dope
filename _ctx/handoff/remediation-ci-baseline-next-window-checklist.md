# Next Agent Checklist

## Start Here
- docs/plans/2026-03-14-ci-baseline-remediation-branch-review-first.md
- apps/pae-wizard/outputs/reviewctl/ci-baseline-pr-mypy.md
- apps/pae-wizard/outputs/reviewctl/ci-baseline-main-mypy.md

## Guardrails
- Respect the active constraints.

## Recommended Order
- Read the checkpoint and handoff only.
- Verify the active blocker with fresh evidence.
- Continue on the narrowest remaining path.

## Current Status Snapshot
- Branch: codex/wo-remediation-ci-baseline
- HEAD: a8fed59d0edaa1b27f1fbc7eb75937a6a5dc85d2
- Repo/worktree root: /Users/felipe_gonzalez/Developer/agent_h/.worktrees/remediation-ci-baseline/trifecta_dope
- Review findings: closed
- `_ctx/index/wo_worktrees.json`: reviewed and discarded from this branch
- Durable staged scope: code fixes plus tracking docs
- Remaining technical blocker: `uv run mypy src/`

## Stop Conditions
- Stop if the next step reopens an out-of-scope front.
- Stop if the only path forward requires unsafe manual state changes.
