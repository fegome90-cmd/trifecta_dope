# Archive Report: publish-main-backlog

**Archived**: 2026-05-22
**Status**: completed

## Summary

Resolved 12 unpushed commits + dirty working tree. Deleted stale test file, gitignored reconcile.patch (133K lines), committed metadata drift, pushed 17 commits to origin/main.

## Commits Added

- `77ddaccd` fix(tests): remove stale test_daemon_manager.py
- `aaeda12f` chore: gitignore generated reconcile.patch fixture (-133,803 lines)
- `38057871` chore: commit metadata drift, formatting, and pyrightconfig
- `68cf5090` docs: add SDD artifacts for publish-main-backlog and git-hygiene-cleanup
- `b6a0b656` chore: ctx sync post-SDD artifacts

## Verification

- `git rev-list --left-right --count origin/main...main` → `0 0`
- `test -f tests/unit/test_daemon_manager.py` → fails (deleted)
- `test -f tests/unit/test_daemon_manager_unit.py` → succeeds
- `git ls-files | grep reconcile.patch` → empty (untracked)
- 2019 tests collected, 0 errors

## Residual Follow-ups

- `precommit-ctx-sync-fix` — hook regex causes dirty loop with \_ctx/generated/ and \_ctx/telemetry/
- `ctx-generated-artifacts-gitignore-policy` — evaluate if \_ctx/generated/ and \_ctx/telemetry/ should be fully gitignored
