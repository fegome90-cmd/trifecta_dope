# Design: publish-main-backlog

No architectural decisions — this is operational. Key design choices:

## DEC-01: Separate commits per concern

| Commit | Type         | Content                                                     |
| ------ | ------------ | ----------------------------------------------------------- |
| 1      | `fix(tests)` | Delete stale `test_daemon_manager.py`                       |
| 2      | `chore`      | .gitignore `reconcile.patch` + untrack                      |
| 3      | `chore`      | Remaining dirty files (formatting, metadata, pyrightconfig) |

**Why separate**: If one commit causes issues, it can be reverted independently. The reconcile.patch gitignore change is irreversible (untracking), so isolating it is critical.

## DEC-02: .gitignore vs keep tracking reconcile.patch

**Chosen**: Add to `.gitignore` and `git rm --cached`.

**Why**: The file regenerates on every ctx rebuild, producing 270K-line diffs. It's a test fixture artifact, not source code. Tracking it adds noise without value.

**Alternative rejected**: Keep tracking and commit the regeneration. Would bloat git history with meaningless diffs every session.

## File change mapping

| File                                | Action            | Commit   | Risk                     |
| ----------------------------------- | ----------------- | -------- | ------------------------ |
| `tests/unit/test_daemon_manager.py` | `git rm`          | Commit 1 | Low — replacement exists |
| `.gitignore`                        | append line       | Commit 2 | Low — additive           |
| `reconcile.patch`                   | `git rm --cached` | Commit 2 | Low — file stays on disk |
| `src/platform/daemon_manager.py`    | stage             | Commit 3 | None — formatting only   |
| `_ctx/*`, `my_project/_ctx/*`       | stage             | Commit 3 | Low — generated metadata |
| `readme_tf.md`, `skill.md`          | stage             | Commit 3 | Low — templates          |
| `pyrightconfig.json`                | `git add`         | Commit 3 | Low — config             |
| `reconcile.log`                     | stage             | Commit 3 | None — trivial           |
