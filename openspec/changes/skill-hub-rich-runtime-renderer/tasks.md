# Tasks: skill-hub rich runtime renderer

## Phase 1: Red — renderer contract tests

**Skills:** `$sdd-tasks`, `$authority-flow-audit`

- [x] 1.1 Add/extend tests proving TTY runtime card rendering uses a governed rich renderer while non-TTY rendering remains plain.
- [x] 1.2 Add/extend tests proving rich and plain rendering consume the same semantic card model and preserve outcome/identity parity.
- [x] 1.3 Add/extend promotion/verify tests proving rich-renderer artifacts are included in the promoted set and fail closed when missing, malformed, or mismatched.
- [x] 1.4 Add/extend tests forbidding promoted runtime imports from `src/cli/*` for card rendering.

## Phase 2: Green — governed rich renderer implementation

**Skills:** `$authority-flow-audit`, `$python-cli-patterns`

- [x] 2.1 Modify `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill_hub_runtime_ux.py` to add governed rich card rendering for TTY while preserving plain rendering for non-TTY.
- [x] 2.2 Modify `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill_hub_cards_core.py` to route renderable cards through rich or plain presentation mode without moving semantic authority out of core.
- [x] 2.3 Modify `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill-hub-cards` only if needed to keep the runtime adapter aligned with the governed renderer contract.
- [x] 2.4 Modify `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill-hub-runtime` only if needed so the canonical artifact map and verify logic fully cover the rich renderer surface.

## Phase 3: Parity and promotion validation

**Skills:** `$sdd-verify`, `$authority-flow-audit`

- [x] 3.1 Update `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/tests/unit/test_skill_hub_cards_governed.py` to validate governed rich runtime output expectations for TTY paths.
- [x] 3.2 Update `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/tests/unit/test_skill_hub_render_parity.py` to prove rich/plain formatting differences do not alter semantic card identity or degraded-state visibility.
- [x] 3.3 Update `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/tests/unit/test_skill_hub_runtime_promotion.py` to validate promoted rich renderer completeness and fail-closed verification behavior.
- [x] 3.4 Update `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/tests/unit/test_skill_hub_runtime_ux.py` to validate intro/banner plus rich/plain renderer helpers under TTY and non-TTY conditions.

## Phase 4: Runtime verification and smoke checks

**Skills:** `$verification-before-completion`, `$authority-flow-audit`

- [x] 4.1 Run a focused pytest slice for runtime UX, governed cards, parity, and promotion.
- [x] 4.2 Promote the governed runtime and verify the receipt-backed installed artifact set still passes fail-closed verification.
- [x] 4.3 Run a real TTY smoke check showing `skill-hub --cards "query"` uses governed rich cards while preserving plain behavior for non-TTY flows.
- [x] 4.4 Update apply/verify artifacts with exact commands, outputs, and any remaining warnings.
