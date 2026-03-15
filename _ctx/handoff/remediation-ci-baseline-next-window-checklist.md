# Next Agent Checklist

## Start Here
- docs/plans/2026-03-14-ci-baseline-remediation-branch-review-first.md
- _ctx/checkpoints/2026-03-15/checkpoint_141935_ci-baseline-mypy-green-next-branch-review.md
- _ctx/handoff/remediation-ci-baseline-next-window.md
- apps/pae-wizard/outputs/reviewctl/ci-baseline-pr-mypy.md
- apps/pae-wizard/outputs/reviewctl/ci-baseline-main-mypy.md

## Guardrails
- Respect the active constraints.
- Keep the three type-fix commits closed: e1e812d, c97306d, 962ca28.
- Do not reopen `_ctx/index/wo_worktrees.json`.

## Recommended Order
- Read the checkpoint and handoff only.
- Confirm the docs-only `_ctx` closeout is committed or finish it cleanly.
- Move to branch-review / PR validation now that `uv run mypy src/` is green.

## Current Status Snapshot
- {'branch': 'codex/wo-remediation-ci-baseline', 'head': '962ca28146fe49d911b8f22fa42d4e5752465e9d', 'workspace_bundle': {'repo': '/Users/felipe_gonzalez/Developer/agent_h/.worktrees/remediation-ci-baseline/trifecta_dope'}, 'code_worktree_clean': True, 'mypy_src_green': True, 'next_phase': 'branch-review'}

## Stop Conditions
- Stop if the next step reopens an out-of-scope front.
- Stop if the only path forward requires unsafe manual state changes.
