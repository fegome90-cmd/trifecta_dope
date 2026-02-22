# WO-0051 Decision - Dirty Zombie Resolution

**Date:** 2026-02-21
**Status:** DECIDED - PRESERVE PATCH + CLEANUP
**Decision:** DESTROY worktree (changes are segment context files, not critical)

## Evidence

### Worktree State
```
 D _ctx/agent.md
 D _ctx/agent_trifecta_dope.md
 D _ctx/prime_trifecta_dope.md
 D _ctx/session_trifecta_dope.md
?? _ctx/agent_wo-0051.md
?? _ctx/prime_wo-0051.md
?? _ctx/session_wo-0051.md
```

### Patch Analysis
- File: `_ctx/handoff/WO-0051/dirty.patch`
- Lines: 1704
- Content: Segment context file renames (agent, prime, session)

### WO State
- Current: `done` (in `_ctx/jobs/done/WO-0051.yaml`)
- Worktree: Still exists (zombie)

## Decision Rationale

1. Changes are **context file renames** - not code changes
2. Pattern suggests someone tried to isolate segment context for WO-0051
3. WO is `done` - work was completed
4. No critical code at risk

## Action Taken

- [x] Patch saved to `_ctx/handoff/WO-0051/dirty.patch`
- [ ] Worktree removed via `git worktree remove --force`
- [ ] Branch retained (may contain completed work)

## Policy Applied

**GC Policy for Dirty Zombies:**
- Context file changes → Preserved in patch, safe to cleanup
- If segment isolation was intentional → User can restore from patch
- When in doubt → Patch first, then force-remove

---

**Approved by:** Ops Stabilization Session (2026-02-21)
