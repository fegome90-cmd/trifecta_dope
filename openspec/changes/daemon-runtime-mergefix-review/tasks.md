# Tasks: daemon-runtime mergefix review

## Phase 1 — Rescue the bundle
- [x] Identify the leftover daemon/runtime files mixed into `skill-hub-authority-anchor-mergefix`.
- [x] Separate them conceptually from generated noise and minor hygiene edits.
- [x] Create a standalone review change for the rescued bundle.

## Phase 2 — Review follow-up
- [ ] Decide whether the rescued daemon/runtime bundle should be migrated into a fresh worktree/branch or discarded.
- [ ] If accepted, move the bundle to a dedicated implementation surface with its own verification plan.
- [ ] Only after that decision, allow deletion of `skill-hub-authority-anchor-mergefix`.
