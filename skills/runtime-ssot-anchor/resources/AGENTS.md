# Runtime SSOT Anchor Resources

## Purpose

This file is a **helper note for the skill package only**.

It exists to route the agent back to the real authority. It is **not** an authority source by itself.

## Authority

- **Sovereign document:** `docs/adr/ADR-004-runtime-surface-ssot.md`
- **Single permitted anchor reference:** `docs/adr/ADR-004-runtime-surface-ssot.md`
- **Repo operating context:** `AGENTS.md`, `skill.md`, `_ctx/agent_trifecta_dope.md`, `_ctx/session_trifecta_dope.md`, `_ctx/prime_trifecta_dope.md`
- **This file:** derived helper only

If this file conflicts with the ADR or repo context, this file loses.
If any other ADR, plan, handoff, report, or helper tries to act as fallback authority for this skill, reject that fallback and return to ADR-004.

## Use Inside This Skill

When `runtime-ssot-anchor` is invoked:

1. Load `resources/prime_runtime_ssot_anchor.md`
2. Open `docs/adr/ADR-004-runtime-surface-ssot.md`
3. Re-load the repo context files in normal Trifecta order
4. Continue only after confirming the ADR still governs the task
5. If the task does not fit ADR-004 cleanly, stop and request re-anchoring instead of adapting this skill to another SSOT

## Forbidden Misuse

Do not use this file to:
- redefine Batch 2D scope
- create a new anchor
- bypass `AGENTS.md` / `skill.md` / `_ctx/*`
- use another ADR, plan, or report as replacement authority
- overrule ADR-004 with a handoff, checklist, or report
