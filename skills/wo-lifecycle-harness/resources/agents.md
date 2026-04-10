# Agent Rules — WO Lifecycle Harness

## Mission

Keep local WO lifecycle work aligned to the approved anchor and prevent local execution context from becoming program authority.

## Must Do

- Read the anchor first
- Confirm objective, active phase, relevant irreversible decision, local guardrail, and roadmap/ownership impact before local intervention
- Keep local analysis scoped to the touched surface
- Treat the anchor as roadmap authority and local runtime surfaces as execution surfaces

## Must Not Do

- Do not duplicate roadmap content from the anchor
- Do not duplicate irreversible decisions from the anchor
- Do not duplicate certified state from the anchor
- Do not treat wrappers or rescue surfaces as lifecycle owners
- Do not declare global closure from local fixes

If the work changes roadmap, ownership, closure criteria, or a normative reference, it is not a simple local fix; state the impact on the anchor and/or ADR surface explicitly.

## Load Order

1. Anchor
2. `agents.md`
3. `prime.md`
4. Local problem artifact

## Short Resume Contract

Return this shape before local work:

- objective loaded
- active phase loaded: `<phase>`
- irreversible decision relevant to this task: `<decision>`
- local guardrail loaded: `<guardrail>`
- task touches roadmap/ownership: yes/no

## Active Operational Guardrail

Current main risk: a local change accidentally makes a transitional surface read like a happy-path owner, blurring the single-owner lifecycle contract.
