# Tasks: publish-main-backlog

## Phase 1: Verify

### T1.1: Audit 12 unpushed commits

- **REQ**: REQ-01
- **Action**: `git log origin/main..main --oneline` — verify each commit is clean, atomic, no secrets
- **Verify**: All 12 commits have clear messages, no WIP markers, no hardcoded secrets

## Phase 2: Commit cleanup

### T2.1: Delete stale test file

- **REQ**: REQ-02
- **Action**: `git rm tests/unit/test_daemon_manager.py && git commit -m "fix(tests): remove stale test_daemon_manager.py (replaced by test_daemon_manager_unit.py)"`
- **Verify**: `git show HEAD:tests/unit/test_daemon_manager.py` fails, `git show HEAD:tests/unit/test_daemon_manager_unit.py` succeeds

### T2.2: .gitignore reconcile.patch

- **REQ**: REQ-03
- **Action**:
  1. Append `tests/fixtures/reconcile/running_wo_without_worktree/_ctx/logs/reconcile/reconcile.patch` to `.gitignore`
  2. `git rm --cached tests/fixtures/reconcile/running_wo_without_worktree/_ctx/logs/reconcile/reconcile.patch`
  3. `git add .gitignore && git commit -m "chore: gitignore generated reconcile.patch fixture"`
- **Verify**: `git ls-files reconcile.patch` returns empty

### T2.3: Commit remaining dirty files

- **REQ**: REQ-04
- **Action**:
  1. **Verify exact file list** before staging: `git diff --name-only HEAD -- src/platform/daemon_manager.py _ctx/ my_project/_ctx/ readme_tf.md skill.md pyrightconfig.json tests/fixtures/reconcile/running_wo_without_worktree/_ctx/logs/reconcile/reconcile.log`
  2. Confirm output matches this list (abort if extra files appear):
     ```
     _ctx/agent_trifecta_dope.md
     _ctx/generated/repo_map.md
     _ctx/generated/symbols_stub.md
     _ctx/index/wo_worktrees.json
     _ctx/prime_trifecta_dope.md
     _ctx/session_trifecta_dope.md
     _ctx/telemetry/events.jsonl
     _ctx/telemetry/last_run.json
     my_project/_ctx/telemetry/events.jsonl
     my_project/_ctx/telemetry/last_run.json
     readme_tf.md
     skill.md
     src/platform/daemon_manager.py
     tests/fixtures/reconcile/running_wo_without_worktree/_ctx/logs/reconcile/reconcile.log
     ```
  3. Stage **explicit file list only** (NO blanket `git add _ctx/`):
     ```
     git add \
       src/platform/daemon_manager.py \
       _ctx/agent_trifecta_dope.md \
       _ctx/generated/repo_map.md \
       _ctx/generated/symbols_stub.md \
       _ctx/index/wo_worktrees.json \
       _ctx/prime_trifecta_dope.md \
       _ctx/session_trifecta_dope.md \
       _ctx/telemetry/events.jsonl \
       _ctx/telemetry/last_run.json \
       my_project/_ctx/telemetry/events.jsonl \
       my_project/_ctx/telemetry/last_run.json \
       readme_tf.md \
       skill.md \
       pyrightconfig.json \
       tests/fixtures/reconcile/running_wo_without_worktree/_ctx/logs/reconcile/reconcile.log
     ```
  4. `git commit -m "chore: commit metadata drift, formatting, and pyrightconfig"`
- **Verify**: `git status --short` returns empty

## Phase 3: Push

### T3.1: Push to origin

- **REQ**: REQ-05
- **Action**: `git push origin main`
- **Verify**: `git rev-list --left-right --count origin/main...main` returns `0 0`

## Verification Gate

- `git status --short` → clean
- `git log origin/main..main --oneline` → empty
- `test -f tests/unit/test_daemon_manager.py` → fails (deleted)
- `test -f tests/unit/test_daemon_manager_unit.py` → succeeds
