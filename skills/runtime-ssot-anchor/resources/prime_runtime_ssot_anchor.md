# Prime: runtime-ssot-anchor

**Role:** Pre-flight re-entry checklist  
**Derived from:** `docs/adr/ADR-004-runtime-surface-ssot.md`  
**Authority:** None. If anything here conflicts with ADR-004, ADR-004 wins.

---

## Mandatory Load Order

1. `docs/adr/ADR-004-runtime-surface-ssot.md`
2. `AGENTS.md`
3. `skill.md`
4. `_ctx/agent_trifecta_dope.md`
5. `_ctx/session_trifecta_dope.md` (skim)
6. `_ctx/prime_trifecta_dope.md` (reference)

## Single-SSOT Gate

- Allowed SSOT: `docs/adr/ADR-004-runtime-surface-ssot.md`
- Allowed anchor reference: `docs/adr/ADR-004-runtime-surface-ssot.md`
- Forbidden fallback: any other ADR, plan, handoff, report, or helper note unless ADR-004 explicitly sends you there
- If the current task appears to belong to another SSOT, **stop and ask for re-anchoring**

## Re-entry Checks

- [ ] I am treating ADR-004 as the **one SSOT** for Batch 2D runtime ownership
- [ ] I am treating ADR-004 as the **one ancla** for this documentary task
- [ ] I am not using any second ADR or document as fallback authority
- [ ] I understand this phase is documentation-first, not a runtime bugfix
- [ ] I will not treat plans, handoffs, reports, or this skill as co-equal authority
- [ ] I will not edit `src/platform/runtime_manager.py` or `src/trifecta/platform/runtime_manager.py` without new verifiable evidence
- [ ] I will report conflicts instead of silently reconciling them

## Derived Artifacts to Demote on Re-entry

These can support execution, but they cannot legislate:

- `docs/plans/2026-03-27-batch-2d-runtime-ssot-design-plan.md`
- `_ctx/handoff/handoff_2026-03-27_batch-2d-runtime-manager-ssot-design.md`
- `_ctx/handoff/next-agent-checklist_2026-03-27_batch-2d-runtime-manager-ssot-design.md`
- `docs/reports/2026-03-27-runtime-surface-ssot-evidence.md`
- `skills/runtime-ssot-anchor/**`

## Abort Conditions

Stop and escalate if:
- ADR-004 is missing or unread
- a derived document is being used to override ADR-004
- another ADR or document is proposed as backup SSOT for this skill
- the requested action implies runtime code edits without fresh evidence
- multiple documents are being treated as parallel SSOTs
- the task context no longer matches ADR-004 and needs re-anchoring
