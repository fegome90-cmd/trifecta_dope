# Backlog + Work Orders Pipeline

## State machine

Work orders move through these states:

- `pending` -> `running` -> `done`
- `pending` -> `running` -> `failed`

A WO can only be `done` when its DoD artifacts are complete.

## Traceability invariants

- `backlog.yaml` is canonical for epics and WO queue.
- Each WO in `_ctx/jobs/{pending,running,done,failed}` must reference a valid `epic_id` and `dod_id`.
- Every WO must define `scope.allow` and `scope.deny` plus `verify.commands`.
- Context pack sources live under `_ctx/`; legacy stubs such as `_ctx/blacklog/README.md` are non-canonical.

## Rollback

- All changes are additive; rollback is a git revert.
- If state diverges (locks/worktrees), use `scripts/ctx_reconcile_state.py` to repair before any manual edits.
