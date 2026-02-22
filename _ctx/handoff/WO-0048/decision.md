# WO-0048 Decision - Dirty Zombie Resolution

**Date:** 2026-02-21
**Status:** DECIDED - CLEANUP APPROVED
**Decision:** DESTROY (worktree contains only telemetry noise)

## Evidence

### Worktree State
```
M _ctx/telemetry/events.jsonl
M _ctx/telemetry/last_run.json
```

### Patch Analysis
- File: `_ctx/handoff/WO-0048/dirty.patch`
- Lines: 357
- Content: Telemetry events only (no code/logic changes)

### WO State
- Current: `failed` (in `_ctx/jobs/failed/WO-0048.yaml`)
- Worktree: Still exists (zombie)

## Decision Rationale

1. Changes are **telemetry noise** only - no code, no docs, no valuable work
2. WO is in `failed` state - work was abandoned
3. Patch preserved for audit trail
4. No value in keeping worktree alive

## Action Taken

- [x] Patch saved to `_ctx/handoff/WO-0048/dirty.patch`
- [ ] Worktree removed via `git worktree remove --force`
- [ ] Branch retained (contains commits, may have value)

## Policy Applied

**GC Policy for Dirty Zombies:**
- Telemetry-only changes → Safe to destroy
- Code/docs changes → Requires review
- When in doubt → Preserve patch and force-remove

---

**Approved by:** Ops Stabilization Session (2026-02-21)
