# Tasks: git-hygiene-cleanup

**Prerequisite**: `publish-main-backlog` completed.

## Phase 1: Re-validate

### T1.1: Fetch and re-check remote state

- **REQ**: REQ-01
- **Action**:
  1. `git fetch origin --prune`
  2. Re-check: `git branch -r --no-merged main` — list current stale branches
  3. Re-check: `gh pr list --repo fegome90-cmd/trifecta_dope --state open` — verify PR states
  4. Re-check: `gh pr checks 106 --repo fegome90-cmd/trifecta_dope` and same for 104
- **Verify**: Stale branch list matches spec. If any branch was merged/updated, skip it.

## Phase 2: Close PRs and delete branches

### T2.1: Close Dependabot PR #106 (pyright)

- **REQ**: REQ-02
- **Action**: `gh pr close 106 --repo fegome90-cmd/trifecta_dope --comment "Closing stale Dependabot PR — CI failing, will re-trigger after main stabilization."`
- **Verify**: PR #106 state is CLOSED

### T2.2: Close Dependabot PR #104 (dependency-review-action)

- **REQ**: REQ-02
- **Action**: Same as T2.1 for PR #104
- **Verify**: PR #104 state is CLOSED

### T2.3: Delete stale remote branches (4 + 2 dependabot)

- **REQ**: REQ-02, REQ-03
- **Action**:
  1. Delete codex branches individually (any already-gone branch won't block others):
     ```
     git push origin --delete codex/batch-2d-runtime-manager || echo "already gone"
     git push origin --delete codex/wo-frictionless-closeout || echo "already gone"
     git push origin --delete codex/wo-remediation-ci-baseline || echo "already gone"
     ```
  2. Delete user branch:
     ```
     git push origin --delete fegome90-cmd/wo-0015-work || echo "already gone"
     ```
  3. Delete dependabot branches (after PR close, may already be deleted by GitHub):
     ```
     git push origin --delete dependabot/github_actions/actions/dependency-review-action-5 || echo "already gone"
     git push origin --delete dependabot/pip/pyright-1.1.409 || echo "already gone"
     ```
  4. `git remote prune origin`
- **Verify**: `git branch -r --no-merged main` shows only hygiene/\* + origin/main

### T2.4: Verify hygiene branches preserved

- **REQ**: REQ-04
- **Action**: `git branch -r | grep hygiene`
- **Verify**: Both `hygiene/git-audit-20260504` and `hygiene/stash-preserve-codex-freeze` present

## Phase 3: Local cleanup

### T3.1: Prune orphan worktree

- **REQ**: REQ-05
- **Action**:
  1. `rm -rf .worktrees/review-pr-hygiene-campaign-closeout`
  2. `git worktree prune`
- **Verify**: `git worktree list` shows exactly 1 entry

### T3.2: Drop stale stash

- **REQ**: REQ-06
- **Action**: `git stash drop stash@{0}`
- **Verify**: `git stash list` returns empty

### T3.3: Delete obsolete tags

- **REQ**: REQ-07
- **Action**:
  1. `git tag -d archive/dirty-main-2026-01-06 backup/wip-fulltext-fallback-audit pre-merge-WO-0045-20260213-202041`
  2. `git push origin :refs/tags/archive/dirty-main-2026-01-06 :refs/tags/backup/wip-fulltext-fallback-audit :refs/tags/pre-merge-WO-0045-20260213-202041`
- **Verify**: `git tag -l` shows only `stash-preserve-codex-freeze-v1`

### T3.4: Garbage collect

- **REQ**: REQ-08
- **Action**: `git gc --prune=now`
- **Verify**: `git count-objects -vH` shows garbage: 0

## Verification Gate

- `git branch -r --no-merged main` → only `hygiene/*` branches
- `git worktree list` → 1 worktree
- `git stash list` → empty
- `git tag -l` → only `stash-preserve-codex-freeze-v1`
- `git count-objects -vH` → garbage: 0
- `gh pr list --repo fegome90-cmd/trifecta_dope --state open` → empty
