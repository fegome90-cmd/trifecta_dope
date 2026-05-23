# Proposal: git-hygiene-cleanup

**Intent**: Clean up stale git references — remote branches, orphan worktree, stale stash, obsolete tags, and garbage objects. Runs AFTER publish-main-backlog.

**Scope**: Git housekeeping only. No commits, no pushes, no source code changes.

**Approach**: Sequential destructive operations with SHA recovery records, gated by re-validation of remote state before each deletion.

## Prerequisites

- **BLOCKED BY**: `publish-main-backlog` MUST be completed first (origin/main must be current before closing PRs or deleting branches)

## Problems

### P1: 5 stale remote branches (PRs CLOSED or no PR)

| Branch                                      | Last Activity | PR State             | SHA                              |
| ------------------------------------------- | ------------- | -------------------- | -------------------------------- |
| `codex/batch-2d-runtime-manager`            | 8 weeks       | CLOSED (#81)         | `d91a01ad`                       |
| `codex/wo-frictionless-closeout`            | 9 weeks       | No PR                | `c9fca10a`                       |
| `codex/wo-remediation-ci-baseline`          | 10 weeks      | CLOSED (#78)         | `15761042`                       |
| `fegome90-cmd/wo-0015-work`                 | 3 months      | CLOSED               | `3c594fa2`                       |
| `dependabot/.../dependency-review-action-5` | 3 weeks       | OPEN (#104) CI fails | `09cebfa4`                       |
| `dependabot/.../pyright-1.1.409`            | 11 days       | OPEN (#106) CI fails | (new branch, fetched post-audit) |

### P2: 2 hygiene branches to PRESERVE (not delete)

| Branch                                | Content                                    | Decision                         |
| ------------------------------------- | ------------------------------------------ | -------------------------------- |
| `hygiene/git-audit-20260504`          | 7 unique commits of git hygiene audit docs | **PRESERVE** — historical record |
| `hygiene/stash-preserve-codex-freeze` | Full repo snapshot with deleted sources    | **PRESERVE** — recovery point    |

### P3: Orphan worktree

- `.worktrees/review-pr-hygiene-campaign-closeout/` — points to main, no separate branch

### P4: Stale stash

- `stash@{0}`: session log + uv.lock from 13 days ago, verified superseded by main

### P5: 3 obsolete tags (1 preserved)

| Tag                                  | Age      | Decision                             |
| ------------------------------------ | -------- | ------------------------------------ |
| `archive/dirty-main-2025-01-06`      | 5 months | DELETE                               |
| `backup/wip-fulltext-fallback-audit` | 5 months | DELETE                               |
| `pre-merge-WO-0045-20260213-202041`  | 3 months | DELETE                               |
| `stash-preserve-codex-freeze-v1`     | 3 weeks  | KEEP (aligned with preserved branch) |

### P6: Garbage objects

- 2 garbage temp objects (13.71 MiB), 33 prune-packable

## Non-goals

- Publishing commits or pushing (done in publish-main-backlog)
- Modifying source code
- Force-pushing or rewriting history

## Rollback

- Deleted remote branches: `git push origin <sha>:refs/heads/<name>` to restore
- Deleted tags: `git tag <name> <sha> && git push origin <tag>`
- Worktree: can be recreated
- Stash: cannot be restored (content verified in main)
