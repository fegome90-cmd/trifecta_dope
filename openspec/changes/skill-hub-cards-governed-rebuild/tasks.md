# Tasks: skill-hub cards governed rebuild

## Phase 1 — Rebuild the verified cards slice
- [x] Restore `scripts/skill-hub` support for `--cards` and `--limit`.
- [x] Replace the standalone `scripts/skill-hub-cards` implementation with a thin governed entrypoint.
- [x] Carry `scripts/skill_hub_cards_core.py` as the sole home for cards parsing/classification/rendering.
- [x] Keep `scripts/skill_hub_cards.py` as a deprecated shim only.

## Phase 2 — Lock behavior with evidence
- [x] Add wrapper contract tests for exit and stream propagation.
- [x] Add governed runtime tests for renderable, metadata-only, unsupported, and mixed-result batches.
- [x] Verify the targeted governed tests pass on the clean rebuild worktree.

## Phase 3 — Closeout discipline
- [x] Re-audit this rebuilt slice against the canonical SSOT and anchor before archive.
- [ ] Clean up transient forensic worktrees/branches/stash once the rebuilt surface is the accepted authority.
