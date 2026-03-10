# Phase 6.5 — Minimal canonicalization and duplicate curation for `skill-hub`

## Scope
Ola 1 only.

This is not a renaming project. It is a minimal proposal for:
- obvious duplicate handling
- visible canonical entry selection
- limited demotion of noisy prefixed variants

## Evidence base
Observed problematic visible prefixes in Phase 6:
- `examen-*`
- `plugin-*`
- `superpowers-*`
- `official-*`
- `adr-*`

Observed cases:
- `q01`: `examen-dispatching-parallel-agents`, `superpowers-dispatching-parallel-agents`
- `q05`: `plugin-metodo-tdd-first-python`, `superpowers-systematic-debugging`
- `q12`: `adr-agents-plugin`
- `q08`: `examen-branch-review-api`

## Canonicalization principles
1. Prefer an existing manifest-backed skill with stable, reusable task semantics.
2. Prefer non-source-prefixed visible names when a canonical name exists.
3. Do not demote a duplicate if it is the only visible manifestation of a valid concept.
4. Do not attempt global mass renaming in Ola 1.

## Proposal table

| Family / case | Current visible variants | Proposed canonical visible entry | Duplicate action | Why |
|---|---|---|---|---|
| dispatching parallel agents | `examen-dispatching-parallel-agents`, `superpowers-dispatching-parallel-agents` | `dispatching-parallel-agents` | demote prefixed duplicates behind canonical visible entry | Duplicate semantics; prefixed forms add source noise. |
| python testing | `python-testing` (pi), `python-testing` (claude) | `python-testing` | keep one canonical visible entry, demote duplicate source variant | Same name and same semantics. |
| tdd workflow | `tdd-workflow` (pi), `tdd-workflow` (claude) | `tdd-workflow` | keep one canonical visible entry, demote duplicate source variant | Same name and same semantics. |
| strategic compact | `strategic-compact` (pi), `strategic-compact` (claude) | `strategic-compact` | keep one canonical visible entry, demote duplicate source variant | Same name and same semantics. |
| learned PR feedback | `learned-pr-feedback-resolution` (pi), `learned-pr-feedback-resolution` (codex) | `learned-pr-feedback-resolution` | keep one canonical visible entry, demote duplicate source variant | Same functional meaning. |
| branch review API | `branch-review-api` (pi), `examen-branch-review-api` (retrieved surface) | `branch-review-api` | demote prefixed examen variant | Same domain, prefixed variant contaminates top positions. |
| systematic debugging | `superpowers-systematic-debugging` only | `superpowers-systematic-debugging` for now | leave intact in Ola 1 | No canonical unprefixed manifest entry yet. Defer visible alias/canon creation to later curational pass if needed. |
| ADR agents plugin | `adr-agents-plugin` | leave intact but not canonical for workflow/agent coordination intent | leave intact | Not a duplicate problem; it is an unrelated high-token competitor. Solve first through metadoc hygiene and later aliases/content, not forced rename. |
| official-* family | `official-figma-code-connect-components` etc. | leave intact | leave intact for now | Noise exists, but direct contamination evidence is weaker than metadocs and obvious duplicates. Avoid broad changes in Ola 1. |

## What not to touch yet
- do not mass-rename `superpowers-*`
- do not mass-rename `plugin-*`
- do not rewrite SKILL.md content yet
- do not add aliases yet

## Minimal Ola 1 actions recommended
1. canonicalize exact duplicate names first:
   - `python-testing`
   - `tdd-workflow`
   - `strategic-compact`
   - `learned-pr-feedback-resolution`
2. canonicalize obvious prefixed duplicate for branch review:
   - prefer `branch-review-api` over `examen-branch-review-api`
3. canonicalize duplicate pair:
   - `dispatching-parallel-agents`

## Expected value
This will not solve all retrieval failures alone.
It should reduce avoidable source-label noise and make E1 easier to interpret causally.

## Status
**pass with issues**
