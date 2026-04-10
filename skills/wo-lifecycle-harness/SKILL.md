---
name: wo-lifecycle-harness
description: Use when working on Trifecta WO lifecycle, harness ownership, verify/finish boundaries, worktree governance, or migration sequencing that must stay bound to the approved lifecycle anchor without duplicating roadmap authority.
---

# WO Lifecycle Harness

## Purpose

This skill binds local WO lifecycle work to the approved program anchor before touching any local problem surface.

The anchor is the program source of truth.
This skill is intentionally thin: it enforces load order, fail-closed authority handling, and a useful pre-intervention resume.

## Path Resolution Rule

Resolve the anchor from the repo root at:

- `docs/plans/WO-LIFECYCLE-HARNESS-ANCHOR.md`

Resolve support resources relative to the skill root:

- `resources/agents.md`
- `resources/prime.md`

Do not resolve these support resources from the cwd or from the repo root.

## Mandatory Load Order

Read in this order before touching any local problem:

1. `docs/plans/WO-LIFECYCLE-HARNESS-ANCHOR.md`
2. `resources/agents.md`
3. `resources/prime.md`
4. Only then inspect the local artifact for the specific problem

## Fail-Closed Rule

If `docs/plans/WO-LIFECYCLE-HARNESS-ANCHOR.md` does not exist at the expected repo-relative path, say so explicitly and stop.

Do not:
- guess another anchor path
- treat a draft local copy as durable authority
- treat a checkpoint, handoff, wrapper, or local note as replacement authority

## Required Report Before Intervention

Before proposing or applying any local change, report:

- objective loaded
- active phase loaded: `<phase>`
- irreversible decision relevant to this task: `<decision>`
- local guardrail loaded: `<guardrail>`
- task touches roadmap/ownership: yes/no

## Note on Authority Scope

This skill validates loading from the expected anchor path, but it does not by itself certify the durability of the current reference carrying that anchor.

## Core Rule

Do not let a local fix, wrapper, rescue path, checkpoint, or batch artifact redefine the lifecycle roadmap, ownership model, or global closeout meaning.

## Must Not Do

- Do not duplicate the roadmap from the anchor
- Do not duplicate irreversible decisions from the anchor
- Do not treat wrappers or rescue surfaces as lifecycle owners
- Do not declare global closure from local fixes
- Do not replace missing anchor authority with local convenience surfaces

## Common Mistakes

- Reading local artifacts before the anchor
- Reporting only “loaded” without naming phase, decision, and guardrail
- Treating compatibility or rescue surfaces as happy-path owners
- Escalating a local remediation into a global lifecycle conclusion
