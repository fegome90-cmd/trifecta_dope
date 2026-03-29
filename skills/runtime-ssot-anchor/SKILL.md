---
name: runtime-ssot-anchor
description: Use when working on Batch 2D runtime SSOT, ownership, or anchor questions and the agent must return to the one authoritative document before planning, editing, or trusting derived artifacts.
---

# Runtime SSOT Anchor

## Overview

This skill is a **re-entry bridge** for Batch 2D runtime SSOT/ancla work in `trifecta_dope`.

It does **not** define authority. It exists only to send the agent back to the already-authoritative documents and to the normal Trifecta context cycle.

## Authority Hierarchy

> **Hard rule:** `SSOT/ancla > repo context > this skill`

1. `docs/adr/ADR-004-runtime-surface-ssot.md`  
   - **The one SSOT and the one ancla for Batch 2D runtime ownership.**
2. `agents.md`, `skill.md`, `_ctx/agent_trifecta_dope.md`, `_ctx/session_trifecta_dope.md`, `_ctx/prime_trifecta_dope.md`  
   - Repo operating context under the ADR.
3. `skills/runtime-ssot-anchor/SKILL.md` + `skills/runtime-ssot-anchor/resources/*`  
   - Helper material only. Never sovereign.

If anything in this skill or its resources conflicts with the ADR or repo context, **this skill loses immediately**.

## Single-Anchor Contract

- **One active SSOT only:** `docs/adr/ADR-004-runtime-surface-ssot.md`
- **One permitted anchor reference only:** `docs/adr/ADR-004-runtime-surface-ssot.md`
- **No fallback authority:** do not switch to another ADR, plan, handoff, report, or helper file as substitute authority
- **Exception:** only read another document as supporting context if ADR-004 explicitly points to it or the user explicitly asks for a comparison; even then, ADR-004 stays sovereign
- **Immediate loss rule:** if this skill, its resources, or any derived artifact suggests a broader or different SSOT, that suggestion is invalid

## When to Use

Use this skill when:
- the user says to **volver al SSOT**, **volver al ancla**, or **rehidratar contexto** for Batch 2D runtime work
- a handoff, plan, report, or checklist is being treated as if it were authoritative
- you are resuming work and need the minimum safe read order before acting
- you are unsure whether runtime code may be edited in this phase
- you need to re-ground the task in the single documentary authority instead of derivative notes

Do **not** use this skill as a replacement for the authoritative ADR.

## Mandatory Re-entry Flow

1. Read `docs/adr/ADR-004-runtime-surface-ssot.md` first.
2. Re-load repo context in this order:
   - `AGENTS.md`
   - `skill.md`
   - `_ctx/agent_trifecta_dope.md`
   - `_ctx/session_trifecta_dope.md` (skim)
   - `_ctx/prime_trifecta_dope.md` (reference)
3. Use `resources/prime_runtime_ssot_anchor.md` as a **pre-flight checklist only**.
4. Use `resources/AGENTS.md` as a **routing note only**.
5. Treat plans, handoffs, reports, checklists, and other ADRs as non-authoritative unless ADR-004 explicitly delegates authority.
6. Do **not** fallback to another ADR or plan because it feels “closer” to the current task.
7. If a derived artifact appears to disagree with ADR-004, stop and cite the conflict instead of “resolving” it ad hoc.
8. If the task context does not clearly match ADR-004 or appears to require a different anchor/SSOT, stop and ask for **re-anchoring** before acting.

## Trifecta-Specific Adaptation

This skill follows the **anchor mindset** without copying `anchor_dope` blindly:

- In this repo, the sovereign document is a numbered ADR under `docs/adr/`, not a new `_ctx/ANCHOR.md` invented by the skill.
- Re-entry goes through the existing Trifecta context files (`agents.md`, `skill.md`, `_ctx/*`).
- The skill package adds helper resources, but those resources are explicitly subordinate to the ADR.

## Non-Goals

This skill must **not**:
- create a second SSOT
- create a second ancla
- bind itself to any ADR other than ADR-004
- reinterpret ADR-004 as optional guidance
- fallback to another ADR, plan, report, or checklist as replacement authority
- authorize edits to `src/platform/runtime_manager.py` or `src/trifecta/platform/runtime_manager.py`
- replace the repo's normal Trifecta context workflow

## Conflict / Re-anchor Protocol

Stop immediately and ask for re-anchoring when any of these happens:

- the user request is about a different ADR, a different SSOT, or a different runtime phase
- a plan, report, handoff, checklist, or helper resource is being treated as co-equal with ADR-004
- another document is proposed as “backup authority” for this skill
- the available context cannot be reconciled with ADR-004 without interpretation drift

In that situation, do **not** improvise. Reply with a short conflict note, cite ADR-004, and ask which anchor should govern the task.

## Quick Checks Before Acting

- Is `docs/adr/ADR-004-runtime-surface-ssot.md` loaded? If not, stop.
- Are you using any anchor reference other than ADR-004? If yes, stop and re-anchor.
- Are you treating a handoff or plan as law? If yes, demote it.
- Are you treating another ADR as fallback authority? If yes, stop.
- Are you about to patch runtime code? If yes, verify that new active-consumer evidence exists first.
- Did a helper resource contradict the ADR? If yes, the helper is wrong.
