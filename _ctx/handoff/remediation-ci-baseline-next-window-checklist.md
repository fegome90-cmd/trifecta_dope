# Next Agent Checklist

## Start Here
- docs/plans/2026-03-14-ci-baseline-remediation-branch-review-first.md
- apps/pae-wizard/outputs/reviewctl/ci-baseline-pr-mypy.md
- apps/pae-wizard/outputs/reviewctl/ci-baseline-main-mypy.md

## Guardrails
- Do not reopen the completed type-fix commits when running branch-review.
- Keep _ctx/index/wo_worktrees.json discarded from this branch.
- If another _ctx-only commit becomes necessary, account for the known ctx-sync hook failure in this worktree.

## Recommended Order
- Read the checkpoint and handoff only.
- Verify the active blocker with fresh evidence.
- Continue on the narrowest remaining path.

## Current Status Snapshot
- {'branch': 'codex/wo-remediation-ci-baseline', 'head': '297fe77c89b3b3c1192f8583c76093763e9f87c0', 'workspace_bundle': {'repo': '/Users/felipe_gonzalez/Developer/agent_h/.worktrees/remediation-ci-baseline/trifecta_dope'}, 'worktree_clean': True, 'mypy_src_green': True, 'next_phase': 'branch-review'}

## Stop Conditions
- Stop if the next step reopens an out-of-scope front.
- Stop if the only path forward requires unsafe manual state changes.
