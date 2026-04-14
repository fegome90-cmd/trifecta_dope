# Cleanup Review: forensic skill-hub surfaces

## Scope
Review each dirty file from the old forensic surfaces before deleting any branch, worktree, or stash.

## Surface A — `skill-hub-authority-anchor-closeout`

### `openspec/changes/skill-hub-functional-validation/proposal.md`
- **Finding**: retrospective narrative from the failed SDD backfill; superseded by the honest rebuild change.
- **Disposition**: discard with the closeout worktree after preserving this review.

### `openspec/changes/skill-hub-functional-validation/specs/skill-hub-authority/spec.md`
- **Finding**: delta spec mixes unverified authority claims (especially the nonexistent manifest migration fix).
- **Disposition**: discard; do not reuse as authority.

### `openspec/changes/skill-hub-functional-validation/design.md`
- **Finding**: design drifted from real code and was part of the failed traceability audit.
- **Disposition**: discard.

### `openspec/changes/skill-hub-functional-validation/tasks.md`
- **Finding**: task list reported completion for work that was not actually present on that surface.
- **Disposition**: discard.

## Surface B — `skill-hub-authority-anchor-mergefix`

### `_ctx/generated/repo_map.md`
- **Finding**: generated stub tied to the mergefix worktree slug/hash.
- **Disposition**: discard as regenerated artifact.

### `_ctx/generated/symbols_stub.md`
- **Finding**: generated stub tied to the mergefix worktree slug/hash.
- **Disposition**: discard as regenerated artifact.

### `_ctx/telemetry/events.jsonl`
- **Finding**: runtime telemetry accumulation; not source of truth.
- **Disposition**: discard.

### `_ctx/telemetry/last_run.json`
- **Finding**: transient runtime state only.
- **Disposition**: discard.

### `scripts/skill-hub`
- **Finding**: contains an early `--cards` wrapper variant, but the authoritative version is now committed on `codex/skill-hub-ssot-rebuild`.
- **Disposition**: discard from mergefix; do not keep as a competing implementation surface.

### `src/application/use_cases.py`
- **Finding**: unrelated generic-build fallback change (`segment_id` fallback path); not part of the skill-hub rebuild slice.
- **Disposition**: isolate into a separate future review if still wanted; DO NOT mix into skill-hub cleanup.

### `src/infrastructure/daemon/lsp_handler.py`
- **Finding**: unrelated daemon/LSP behavior changes (`didOpen`, FAILED-state handling).
- **Disposition**: isolate for separate daemon review; not part of this cleanup.

### `src/platform/daemon_manager.py`
- **Finding**: unrelated daemon singleton-lock refactor from socket bind to lock-file create.
- **Disposition**: isolate for separate daemon review; not part of this cleanup.

### `tests/fixtures/reconcile/running_wo_without_worktree/_ctx/logs/reconcile/reconcile.log`
- **Finding**: generated log artifact.
- **Disposition**: discard.

### `tests/fixtures/reconcile/running_wo_without_worktree/_ctx/logs/reconcile/reconcile.patch`
- **Finding**: huge generated patch artifact; evidence/noise, not source code.
- **Disposition**: discard.

### `tests/integration/daemon/test_daemon_manager.py`
- **Finding**: deleted as part of unrelated daemon test reshaping.
- **Disposition**: isolate with daemon review, not with skill-hub cleanup.

### `tests/integration/daemon/test_daemon_manager_integration.py`
- **Finding**: new untracked daemon integration test paired with the deleted daemon manager test.
- **Disposition**: isolate with daemon review, not with skill-hub cleanup.

### `tests/integration/test_path_canonicalization.py`
- **Finding**: minor unrelated cleanup removing unused local vars.
- **Disposition**: discard or reapply separately later; not worth coupling to this cleanup.

### `tests/integration/test_schema_version.py`
- **Finding**: minor unrelated cleanup removing an unused local var.
- **Disposition**: discard or reapply separately later.

### `tests/unit/test_ctx_wo_gc.py`
- **Finding**: unrelated unit-test cleanup around unused imports/locals.
- **Disposition**: discard or reapply separately later.

## Cleanup rule
- Only Surface A narrative files and Surface B generated/runtime noise are candidates for immediate deletion.
- Surface B daemon/code changes must be handled as a separate review bundle before deleting that worktree.

## Proposed split for `skill-hub-authority-anchor-mergefix`

### Bundle 1 — discard immediately as non-authoritative noise
- `_ctx/generated/repo_map.md`
- `_ctx/generated/symbols_stub.md`
- `_ctx/telemetry/events.jsonl`
- `_ctx/telemetry/last_run.json`
- `tests/fixtures/reconcile/running_wo_without_worktree/_ctx/logs/reconcile/reconcile.log`
- `tests/fixtures/reconcile/running_wo_without_worktree/_ctx/logs/reconcile/reconcile.patch`
- `scripts/skill-hub`

### Bundle 2 — daemon/runtime review bundle (real work, unrelated to skill-hub)
- `src/application/use_cases.py`
- `src/infrastructure/daemon/lsp_handler.py`
- `src/platform/daemon_manager.py`
- `tests/integration/daemon/test_daemon_manager.py`
- `tests/integration/daemon/test_daemon_manager_integration.py`

### Bundle 3 — minor unrelated test hygiene
- `tests/integration/test_path_canonicalization.py`
- `tests/integration/test_schema_version.py`
- `tests/unit/test_ctx_wo_gc.py`

## Current recommendation
- Delete Surface A now: already reviewed and fully superseded.
- Keep Surface B only until Bundle 2 receives an explicit separate decision.
- Do not drop `stash@{0}` until Surface B is resolved, because it remains part of the reconstruction evidence chain.

## Rescue status
- Bundle 2 has now been rescued into a separate review change:
  - `openspec/changes/daemon-runtime-mergefix-review/proposal.md`
  - `openspec/changes/daemon-runtime-mergefix-review/design.md`
  - `openspec/changes/daemon-runtime-mergefix-review/tasks.md`
  - `openspec/changes/daemon-runtime-mergefix-review/review-inventory.md`

## Final cleanup result
- `skill-hub-authority-anchor-closeout` has been removed.
- `skill-hub-authority-anchor-mergefix` has been removed after preserving the rescued daemon/runtime bundle and explicitly discarding Bundles 1 and 3.
- The imported `stash@{0}` residue from the old closeout surface has been dropped.
- Stash drop authorization: approved by the repository owner in this Codex thread on 2026-04-14T14:43:12Z; context included `skill-hub-authority-anchor-closeout`, `skill-hub-authority-anchor-mergefix`, and `codex/skill-hub-ssot-rebuild`.
- The only remaining skill-hub implementation surface is `codex/skill-hub-ssot-rebuild`.
