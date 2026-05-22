# Spec: publish-main-backlog

## Requirements

### REQ-01: Assess and classify all 12 unpushed commits

- **Given** 12 commits on local main not present on origin/main
- **When** assessment runs
- **Then** each commit SHALL be verified: clean, atomic, no secrets, no broken state
- **And** the commit list SHALL be confirmed as publishable before push

### REQ-02: Delete stale test file from HEAD

- **Given** `tests/unit/test_daemon_manager.py` still exists in HEAD (was not deleted in commit 6391d651)
- **And** `tests/unit/test_daemon_manager_unit.py` already exists in HEAD as the replacement
- **And** both files coexist causing potential pytest collection conflicts
- **When** cleanup executes
- **Then** `tests/unit/test_daemon_manager.py` SHALL be deleted
- **And** the delete SHALL be committed as a separate fix commit

### REQ-03: Add reconcile.patch to .gitignore

- **Given** `tests/fixtures/reconcile/running_wo_without_worktree/_ctx/logs/reconcile/reconcile.patch` is a 270K-line generated file tracked in git
- **And** it regenerates on every ctx rebuild, producing massive noisy diffs
- **When** cleanup executes
- **Then** the file SHALL be added to `.gitignore`
- **And** the file SHALL be removed from git tracking via `git rm --cached`
- **And** this SHALL be committed as a separate chore commit

### REQ-04: Commit remaining dirty files (metadata + formatting)

- **Given** the following dirty files are confirmed safe to commit:
  - `src/platform/daemon_manager.py` — ruff formatting only (verified: 1 blank line + 1 line-wrap, zero logic change)
  - `_ctx/*`, `my_project/_ctx/*` — generated metadata from ctx rebuild
  - `readme_tf.md`, `skill.md` — template regeneration
  - `pyrightconfig.json` — new project config
  - `tests/fixtures/.../reconcile.log` — trivial log update
- **When** cleanup executes
- **Then** all listed files SHALL be committed as a chore commit

### REQ-05: Push all commits to origin/main

- **Given** REQ-01 through REQ-04 completed
- **When** `git push origin main` executes
- **Then** `git rev-list --left-right --count origin/main...main` SHALL return `0 0`

## Scenarios

### Scenario S01: Clean working tree after commit

- **Given** REQ-02 through REQ-04 applied
- **When** `git status --short` runs
- **Then** working tree SHALL be clean

### Scenario S02: origin/main up to date

- **Given** REQ-05 applied
- **When** `git log origin/main..main --oneline` runs
- **Then** output SHALL be empty

### Scenario S03: No stale duplicate test file

- **Given** REQ-02 applied
- **When** `test -f tests/unit/test_daemon_manager.py` runs
- **Then** exit code SHALL be non-zero (file deleted)
- **And** `test -f tests/unit/test_daemon_manager_unit.py` SHALL succeed

## Execution Sequence

1. REQ-01: Verify 12 commits are clean
2. REQ-02: Delete stale test file + commit
3. REQ-03: .gitignore reconcile.patch + untrack + commit
4. REQ-04: Commit remaining dirty files
5. REQ-05: Push to origin/main

## Invariants

- INV-01: No production logic change (formatting-only accepted)
- INV-02: No force-push
- INV-03: Each REQ produces a separate atomic commit
- INV-04: Push only happens after all commits are clean and verified
