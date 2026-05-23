# Spec: git-hygiene-cleanup

**Prerequisite**: `publish-main-backlog` completed — origin/main is current.

## Requirements

### REQ-01: Re-validate remote state before destructive operations

- **Given** origin/main was updated by publish-main-backlog
- **When** starting cleanup
- **Then** `git fetch origin --prune` SHALL be run first
- **And** branch list, PR states, and CI status SHALL be re-checked against live data
- **And** any branch that changed state since last audit SHALL be reassessed before deletion

### REQ-02: Close 2 Dependabot PRs with documented reasoning

- **Given** 2 open Dependabot PRs with failing CI:
  - #106: pyright 1.1.408→1.1.409 — CI: Lint/TypeCheck FAIL, Security FAIL, Tests FAIL
  - #104: dependency-review-action 4→5 — CI: Lint/TypeCheck FAIL, Security FAIL, Tests FAIL
- **And** both are against an outdated origin/main (now updated by publish-main-backlog)
- **Decision criteria**: Close if CI still fails after re-check. If CI passes on re-check, reassess.
- **When** cleanup executes
- **Then** each PR SHALL be closed with a comment: "Closing stale Dependabot PR — CI failing, will re-trigger after main stabilization"
- **And** remote branches SHALL be deleted

### REQ-03: Delete 4 stale remote branches with CLOSED PRs

- **Given** after REQ-01 re-validation confirms these are still stale:
  - `codex/batch-2d-runtime-manager` (PR #81 CLOSED) — SHA: `d91a01ad`
  - `codex/wo-frictionless-closeout` (no PR) — SHA: `c9fca10a`
  - `codex/wo-remediation-ci-baseline` (PR #78 CLOSED) — SHA: `15761042`
  - `fegome90-cmd/wo-0015-work` (PR CLOSED) — SHA: `3c594fa2`
- **When** cleanup executes
- **Then** each SHALL be deleted via `git push origin --delete <branch>`
- **And** `git remote prune origin` SHALL clean local tracking refs
- **Safety**: SHAs recorded above for recovery

### REQ-04: Preserve hygiene branches (DO NOT DELETE)

- **Given** `hygiene/git-audit-20260504` and `hygiene/stash-preserve-codex-freeze` contain historical reference data
- **When** cleanup executes
- **Then** these branches SHALL NOT be deleted
- **And** `git branch -r --no-merged main` SHALL still list them after cleanup

### REQ-05: Prune orphan worktree

- **Given** `.worktrees/review-pr-hygiene-campaign-closeout/` exists, points to main, no separate branch
- **When** cleanup executes
- **Then** directory SHALL be removed (`rm -rf .worktrees/review-pr-hygiene-campaign-closeout`)
- **And** `git worktree prune` SHALL run to clean internal refs

### REQ-06: Drop stale stash (verified superseded)

- **Given** `stash@{0}` contains session log + uv.lock changes from 13 days ago
- **And** content verified identical to what already exists in main
- **When** cleanup executes
- **Then** `git stash drop stash@{0}` SHALL be executed

### REQ-07: Delete 3 obsolete tags

- **Given** 3 tags verified obsolete:
  - `archive/dirty-main-2026-01-06` (5 months, cleanup done) — SHA: `c5d8e937`
  - `backup/wip-fulltext-fallback-audit` (5 months, audit done) — SHA: `15bf2a3d`
  - `pre-merge-WO-0045-20260213-202041` (3 months, WO merged) — SHA: `a8766aa9`
- **When** cleanup executes
- **Then** each SHALL be deleted: `git tag -d <tag> && git push origin :refs/tags/<tag>`
- **And** `stash-preserve-codex-freeze-v1` SHALL be kept

### REQ-08: Garbage collect (LAST operation)

- **Given** stash dropped (REQ-06), branches deleted (REQ-02/03), tags deleted (REQ-07)
- **When** cleanup executes
- **Then** `git gc --prune=now` SHALL be run
- **And** `git count-objects -vH` SHALL report 0 garbage

## Scenarios

### Scenario S01: Only active and preserved branches remain

- **Given** all REQs applied
- **When** `git branch -r` runs
- **Then** only the following SHALL appear:
  - `origin/HEAD -> origin/main`
  - `origin/main`
  - `origin/hygiene/git-audit-20260504`
  - `origin/hygiene/stash-preserve-codex-freeze`

### Scenario S02: Single worktree

- **Given** REQ-05 applied
- **When** `git worktree list` runs
- **Then** exactly 1 worktree SHALL be listed

### Scenario S03: No stash

- **Given** REQ-06 applied
- **When** `git stash list` runs
- **Then** output SHALL be empty

### Scenario S04: Reduced repo size

- **Given** REQ-08 applied
- **When** `git count-objects -vH` runs
- **Then** garbage SHALL be 0

## Execution Sequence (MANDATORY)

1. **REQ-01**: Fetch + re-validate (gates all subsequent operations)
2. **REQ-02**: Close Dependabot PRs + delete branches
3. **REQ-03**: Delete stale remote branches
4. **REQ-04**: Verify hygiene branches NOT touched (confirmation only)
5. **REQ-05**: Prune worktree
6. **REQ-06**: Drop stash
7. **REQ-07**: Delete tags
8. **REQ-08**: GC (LAST — after all refs cleaned)

## Invariants

- INV-01: No source code SHALL be modified
- INV-02: No force-push or history rewriting
- INV-03: SHA of every deleted ref recorded in this spec
- INV-04: GC runs LAST, after all ref deletions
- INV-05: `hygiene/*` branches SHALL NOT be deleted
- INV-06: Re-validation (REQ-01) gates all destructive operations
