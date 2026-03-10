# Fase 6.6 Apply — Ola 1 for `skill-hub`

## SSOT vs derived
### SSOT touched
- `data/skill_hub_pilot_queries.yaml`
- `~/.trifecta/segments/skills-hub/prime_skills-hub.md`
- `~/.trifecta/segments/skills-hub/agent_skills-hub.md`
- `~/.trifecta/segments/skills-hub/session_skills-hub.md`
- `~/.trifecta/segments/skills-hub/AGENTS.md`
- `~/.trifecta/segments/skills-hub/README.md`
- `~/.trifecta/segments/skills-hub/_ctx/prime_skills-hub.md`
- `~/.trifecta/segments/skills-hub/_ctx/agent_skills-hub.md`
- `~/.trifecta/segments/skills-hub/_ctx/session_skills-hub.md`
- `~/.trifecta/segments/skills-hub/examen-branch-review-api.md`
- `~/.trifecta/segments/skills-hub/dispatching-parallel-agents.md` (canonical visible entry by rename from examen variant)
- `~/.trifecta/segments/skills-hub/superpowers-dispatching-parallel-agents.md`

### Derived artifacts regenerated, not hand-patched
- `~/.trifecta/segments/skills-hub/_ctx/context_pack.json`
- `~/.trifecta/segments/skills-hub/_ctx/skills_manifest.json`

## Changes applied
### Benchmark reconciliation
Applied directly to `data/skill_hub_pilot_queries.yaml`:
- removed ghost expectations:
  - `methodology-workflows`
  - `work-order-workflows`
  - `root-cause-tracing`
  - `examen-code-review-checklist`
- canonicalized:
  - `systematic-debugging` -> `superpowers-systematic-debugging`
- updated affected queries:
  - `q01`, `q02`, `q03`, `q04`, `q05`, `q09`, `q10`, `q11`, `q12`

### Metadoc hygiene
Hard exclusion via source removal was not viable without patching derived pack state by hand.
Instead, required searchable metadocs were degraded in-place at the SSOT level to minimal administrative text:
- `prime_skills-hub.md`
- `agent_skills-hub.md`
- `session_skills-hub.md`
- `AGENTS.md`
- `README.md`
- plus the `_ctx/prime/agent/session` files that were confirmed to feed the rebuilt root search surface

### Minimal canonicalization
- canonical visible entry kept: `branch-review-api.md`
- duplicate degraded in-place: `examen-branch-review-api.md`
- canonical visible entry created by rename: `dispatching-parallel-agents.md`
- duplicate degraded in-place: `superpowers-dispatching-parallel-agents.md`

## Regeneration flow used
Used existing Trifecta flow only:
1. `uv run trifecta ctx build --segment ~/.trifecta/segments/skills-hub`
2. `uv run trifecta ctx validate --segment ~/.trifecta/segments/skills-hub`

Note:
- `ctx sync` initially surfaced stale-state validation issues while SSOT files were in transition
- after aligning the actual SSOT files, `ctx build` + `ctx validate` completed successfully

## Effective resulting changes
### Context pack changed
Final `context_pack.json` hash:
- `abfbfd439d8287abafe4144cf6dbc96c4eb56d497c93f962a341b098de5005ab`

Observed effective changes in rebuilt context pack:
- `prime_skills-hub.md` -> chars `135`
- `agent_skills-hub.md` -> chars `135`
- `session_skills-hub.md` -> chars `137`
- `AGENTS.md` -> chars `162`
- `README.md` -> chars `161`
- `examen-branch-review-api.md` -> chars `171`
- `superpowers-dispatching-parallel-agents.md` -> chars `191`
- `dispatching-parallel-agents.md` present as canonical visible entry

### Manifest changed or not
`skills_manifest.json` was regenerated/verified, but its hash stayed unchanged:
- `5c853b2492a57f2d6b417218bfbf637d35b049f75529afd331ea9aa5a2058f23`

Interpretation:
- Ola 1 changed the local searchable surface that feeds context-pack retrieval
- it did not alter the external source inventory represented by the manifest

## What was not touched
- Trifecta engine
- production wrapper
- aliases
- external SKILL.md source files outside the segment surface
- E1 execution

## E1 readiness
E1 is **ready from an Ola 1 patch application perspective**, but has **not** been run.

Preconditions now satisfied:
- benchmark no longer expects ghost names
- metadoc surface was degraded at SSOT level
- minimal canonicalization applied at SSOT level
- derived surface regenerated and validated
