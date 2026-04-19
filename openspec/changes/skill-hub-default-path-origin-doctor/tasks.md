# Tasks: skill-hub default path origin doctor

## Phase 1: Red — contract and regression tests

**Skills:** `$sdd-tasks`, `$authority-flow-audit`, `$learned-ownership-scoped-gates`

- [x] 1.1 Add/extend CLI tests for `scripts/skill-hub` so `skill-hub --cards "query"` and `skill-hub "query" --cards` resolve to the same cards route and semantic contract.
- [ ] 1.2 Add/extend acceptance coverage for the default path so `skill-hub "query"` renders governed intro/banner + sentence guidance before search output.
- [x] 1.3 Add/extend runtime verification tests for `scripts/skill-hub-runtime` so missing or drifted required artifacts fail closed using the canonical artifact map.
- [x] 1.4 Add/extend wrapper/runtime tests proving default-path intro/render ownership belongs only to `scripts/skill_hub_runtime_ux.py`, not ad hoc shell banner logic.

## Phase 2: Green — normalize routing and presenter ownership

**Skills:** `$authority-flow-audit`, `$sdd-tasks`

- [x] 2.1 Modify `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill-hub` to normalize argv into one command model before route selection, making `--cards` order-independent.
- [x] 2.2 Modify `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill-hub` so the default path invokes the governed presenter instead of printing any local banner/guidance directly.
- [x] 2.3 Modify `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill-hub-cards` to consume the same admitted query contract as the default path without introducing independent semantics.
- [x] 2.4 Modify `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill_hub_runtime_ux.py` so it is the single writer for default-path intro/render and cards-path framing surfaces.
- [x] 2.5 Modify `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill_hub_cards_core.py` only as needed to preserve shared semantic admission/routing authority across both presentation routes.

## Phase 3: Green — promotion and doctor alignment

**Skills:** `$authority-flow-audit`, `$learned-ownership-scoped-gates`

- [x] 3.1 Modify `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill-hub-runtime` to define one canonical artifact map consumed by both `promote` and `verify`.
- [x] 3.2 Modify `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill-hub-runtime` so promotion publishes the full required runtime set atomically and never a partial authoritative runtime.
- [x] 3.3 Modify `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill-hub-runtime` so `verify` is the operational doctor surface for stale, missing, unreadable, or hash-mismatched artifacts.
- [x] 3.4 Add/adjust receipt/runtime target coverage to prove repo `scripts/` remains SSOT and `~/.local/bin` is delivery target only.

## Phase 4: Refactor and verification

**Skills:** `$sdd-gate-skill`, `$authority-flow-audit`, `$learned-ownership-scoped-gates`

- [x] 4.1 Refactor duplicated route/presenter glue so default and cards paths share one normalized command contract with presentation-only differences.
- [x] 4.2 Re-run focused tests covering CLI parsing, default-path governed intro, cards-path parity, and runtime promote/verify fail-closed behavior.
- [x] 4.3 Re-run the planning gate expectations against the implemented slice: single-writer ownership, canonical artifact map, and doctor-surface authority remain intact.
- [x] 4.4 Update apply-progress / verification artifacts with the exact files touched, evidence run, and any remaining warnings before moving to apply/verify closeout.


## Phase 5: Verification-completion closure slice

**Skills:** `$sdd-tasks`, `$verification-before-completion`, `$sdd-gate-skill`

- [x] 5.1 Add one promoted-runtime or acceptance-level proof that the default path still renders governed intro/guidance after promotion, satisfying the remaining spec scenario for promoted default-path behavior.
- [x] 5.2 Update `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/openspec/changes/skill-hub-default-path-origin-doctor/apply-progress.md` with explicit Strict-TDD cycle evidence so verify does not have to infer RED/GREEN from prose alone.
- [x] 5.3 Produce an explicit post-implementation planning-gate rerun artifact that revalidates single-writer ownership, canonical artifact map, and doctor-surface authority after the code changes.
- [x] 5.4 Re-run `sdd-verify` for this change after the closure evidence is added and confirm the prior CRITICAL/ WARNING findings are resolved or intentionally accepted.
