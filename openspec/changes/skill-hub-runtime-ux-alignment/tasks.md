# Tasks: Skill Hub Runtime UX Alignment

## Phase 1: RED — Boundary and gate lock

- [x] 1.1 Run the pre-apply review with `sdd-gate-skill` against `proposal.md`, `tasks.md`, `specs/skill-hub-authority/spec.md`, and `design.md`; do not proceed while any HIGH or CRITICAL findings remain open.
- [x] 1.2 Extend `tests/unit/test_skill_hub_runtime_promotion.py` to fail if promoted runtime code needs `src/` for intro/error framing.
- [x] 1.3 Add subprocess coverage for `scripts/skill-hub` and `scripts/skill-hub-cards` covering renderable, non-renderable, malformed, and empty-query paths.
- [x] 1.4 Add a fail-closed test for `scripts/skill_hub_runtime_ux.py` missing or malformed, asserting no fallback to `src/` or legacy prose paths is allowed.

## Phase 2: GREEN — Promote runtime UX into scripts/

- [x] 2.1 Create `scripts/skill_hub_runtime_ux.py` with promoted-only intro and error-card helpers that write to stdout/stderr explicitly.
- [x] 2.2 Update `scripts/skill-hub` to use only promoted helpers and remove any `src.cli.*` dependency for runtime framing.
- [x] 2.3 Update `scripts/skill-hub-cards` to consume the promoted UX helper while keeping search/classify/render-plan flow delegated to core.
- [x] 2.4 Update the implementation that defines and verifies the promoted runtime dependency/receipt surface for `scripts/skill_hub_runtime_ux.py`, so the helper’s promoted surface is explicit and testable.

## Phase 3: REFACTOR — Preserve semantic authority in core

- [x] 3.1 Keep `scripts/skill_hub_cards_core.py` as the sole authority for parse/normalize/classify/render-plan/exit-code decisions; move any presentation-only text out of authority paths.
- [x] 3.2 Narrow `src/cli/skill_cards.py` and `src/cli/error_cards.py` to repo-side/reference renderers only, with no promoted-runtime assumptions.
- [x] 3.3 Add an explicit invariant test that copy-only changes in presentation helpers do not alter `RenderPlan` or exit code.

## Phase 4: Verification — Promotion/runtime boundary

- [x] 4.1 Verify `tests/unit/test_skill_hub_runtime_promotion.py` passes with promoted helper dependency explicit and `src/` forbidden in the promoted surface.
- [x] 4.2 Verify the wrapper subprocess tests keep stdout intro, stderr diagnostics, and existing exit codes stable across success and failure cases.
