# Archive Report: git-hygiene-cleanup

**Archived**: 2026-05-22
**Status**: completed

## Summary

Cleaned up stale git references after publish-main-backlog. Closed 2 Dependabot PRs, deleted 6 remote branches, pruned orphan worktree, dropped stale stash, deleted 3 obsolete tags, ran GC.

## Operations Performed

| Operation | Detail |
|-----------|--------|
| PRs closed | #106 (pyright), #104 (dependency-review-action) — CI failing |
| Branches deleted | `codex/batch-2d-runtime-manager`, `codex/wo-frictionless-closeout`, `codex/wo-remediation-ci-baseline`, `fegome90-cmd/wo-0015-work`, 2 dependabot (auto-deleted by GitHub) |
| Branches preserved | `hygiene/git-audit-20260504`, `hygiene/stash-preserve-codex-freeze` |
| Worktree pruned | `.worktrees/review-pr-hygiene-campaign-closeout/` |
| Stash dropped | `stash@{0}` (WIP on main at 49031bd2, verified superseded) |
| Tags deleted | `archive/dirty-main-2025-01-06`, `backup/wip-fulltext-fallback-audit`, `pre-merge-WO-0045-20260213-202041` |
| GC | 624 MiB loose → 0, pack 96→59 MiB |

## Verification

- `git branch -r` → only `origin/main` + 2 `hygiene/*`
- `git worktree list` → 1 worktree
- `git stash list` → empty
- `git tag -l` → `stash-preserve-codex-freeze-v1`
- `git count-objects -vH` → garbage: 0
- `gh pr list --state open` → empty

## Recovery SHA Audit (post-archive)

4 of 6 GC-pruned SHAs recovered and preserved as archive tags:
- `archive/branch-batch-2d-runtime-manager-20260522`
- `archive/branch-wo-remediation-ci-baseline-20260522`
- `archive/branch-wo-0015-work-20260522`
- `archive/tag-wip-fulltext-fallback-audit-20260522`

1 SHA (`c9fca10a`, codex/wo-frictionless-closeout) irrecuperable — documented as ACCEPTED RESIDUAL RISK in `hygiene/recovery-sha-archive-20260522.md`.

## Residual Follow-ups

- `precommit-ctx-sync-fix` — hook regex causes dirty loop
- `ctx-generated-artifacts-gitignore-policy` — evaluate runtime artifact tracking policy
- `recovery-sha-preservation-audit` — 1 SHA permanently lost, policy review needed
- `dependency-mypy-floor-update` — re-trigger Dependabot for pyright after stabilization
- `dependency-typer-gap-assessment` — evaluate Typer version gap
