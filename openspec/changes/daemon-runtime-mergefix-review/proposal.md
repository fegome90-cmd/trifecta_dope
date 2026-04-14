# Proposal: daemon-runtime mergefix review

## Intent
Rescue the unrelated daemon/runtime edits stranded inside `skill-hub-authority-anchor-mergefix` into their own explicit review change so the skill-hub cleanup can proceed without silently discarding potentially valid work.

## Scope

### In Scope
- Inventory the non-skill-hub code changes still present in `skill-hub-authority-anchor-mergefix`.
- Separate daemon/runtime code from generated noise and minor test hygiene.
- Prepare an explicit review bundle for follow-up ownership and decision-making.

### Out of Scope
- Merging or applying those daemon/runtime edits now.
- Reopening the old skill-hub authority narrative.
- Deleting `skill-hub-authority-anchor-mergefix` before the rescued bundle is reviewed.

## Why now
The remaining blocker for final skill-hub closeout is no longer ambiguity; it is a real mixed worktree containing unrelated code. That deserves its own change record instead of being lost during cleanup.
