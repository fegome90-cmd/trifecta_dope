# Proposal: publish-main-backlog

**Intent**: Assess and publish the 12 unpushed commits on main, resolve the dirty working tree, and ensure origin/main is current before any hygiene cleanup.

**Scope**: Push + dirty tree resolution only. No branch deletion, no stash operations, no gc.

**Approach**: Categorize dirty files, commit what belongs, push everything to origin.

## Problems

### P1: 12 unpushed commits on main

- Local main is 12 commits ahead of origin/main (since ~May 14)
- Includes search ranking fixes, test fixes, bug hunt docs, SDD archives
- Risk: data loss if local corrupted

### P2: Dirty working tree — 3 distinct categories of drift

| Category                      | Files                                | Lines changed   | What it is                                                                                     |
| ----------------------------- | ------------------------------------ | --------------- | ---------------------------------------------------------------------------------------------- |
| **Source formatting**         | `src/platform/daemon_manager.py`     | 5               | Ruff auto-format (blank line + line-wrap). Zero logic change.                                  |
| **Missing delete**            | `tests/unit/test_daemon_manager.py`  | -137            | Old file not deleted in commit 6391d651 (only the new file was created). Both coexist in HEAD. |
| **Generated metadata**        | `_ctx/*`, `my_project/_ctx/*`        | ~1,200          | ctx rebuild output, telemetry, session log, generated stubs                                    |
| **Template drift**            | `readme_tf.md`, `skill.md`           | 63              | ctx reset regenerated templates                                                                |
| **Test fixture regeneration** | `tests/fixtures/.../reconcile.patch` | **~404K lines** | Regenerated reconcile patch — tracked in git, massively inflates diff                          |
| **Test fixture log**          | `tests/fixtures/.../reconcile.log`   | 2               | Trivial log update                                                                             |
| **New config**                | `pyrightconfig.json` (untracked)     | 4               | pyright venv config — project-relevant                                                         |

### P3: The reconcile.patch problem

- `tests/fixtures/reconcile/running_wo_without_worktree/_ctx/logs/reconcile/reconcile.patch` is a **270K-line generated diff** tracked in git
- Every ctx rebuild regenerates it, producing a massive diff
- This file should either be `.gitignore`d or committed separately to avoid noise
- It inflates the dirty diff from ~1,300 lines to ~405K lines

## Non-goals

- Deleting remote branches
- Stash or tag operations
- Garbage collection
- Any operation that modifies origin beyond pushing commits

## Rollback

- Commits pushed to origin: `git push origin --force` to revert (requires approval)
- New commit: `git reset HEAD~1` to undo locally
