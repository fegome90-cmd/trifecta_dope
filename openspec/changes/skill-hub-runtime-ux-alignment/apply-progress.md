# Apply Progress — skill-hub-runtime-ux-alignment

## Batch Scope
- Apply batch for Phase 2 (GREEN) + Phase 3 (REFACTOR) within declared ownership files.

## Completed in this batch
- ✅ Added `scripts/skill_hub_runtime_ux.py` as promoted runtime UX surface (intro + structured error cards + runtime text rendering helpers).
- ✅ Updated `scripts/skill-hub` to remove `src.cli.*` runtime imports and route intro/error framing through promoted runtime UX helper.
- ✅ Updated `scripts/skill-hub-cards` into a runtime adapter that delegates semantic execution to `scripts/skill_hub_cards_core.py`.
- ✅ Refactored `scripts/skill_hub_cards_core.py` to keep parse/normalize/classify/render-plan authority while consuming presentation-only helpers from `scripts/skill_hub_runtime_ux.py`.
- ✅ Narrowed `src/cli/skill_cards.py` and `src/cli/error_cards.py` as repo/reference renderers (non-runtime-authority note).
- ✅ Updated `scripts/skill-hub-runtime` canonical receipt/dependency surface to include promoted helper artifact `scripts/skill_hub_runtime_ux.py` (`name=skill-hub-runtime-ux`, `target_name=skill_hub_runtime_ux.py`) and keep wrapper direct-dependency invariants strict/fail-closed.
- ✅ Updated `tests/unit/test_skill_hub_runtime_promotion.py` fixture cloning and receipt assertions to include runtime UX helper as promoted governed artifact.
- ✅ Added invariant test `test_copy_only_presentation_changes_do_not_alter_render_plan_or_exit_code` to lock that presentation-only copy changes do not change semantic `RenderPlan` nor exit code authority.

## Verification run (focused)
- Command:
  - `uv run pytest -q tests/unit/test_skill_hub_runtime_promotion.py tests/unit/test_skill_hub_cards_wrapper_contract.py`
- Outcome:
  - ✅ GREEN — `25 passed in 1.90s`
  - ✅ Promotion receipt includes runtime UX helper and verify remains fail-closed when helper is missing.
  - ✅ Wrapper/card contract tests stay green with unchanged stream/exit-code behavior.

## Pending after this batch
- None for owned tasks (2.4, 3.3, 4.1 closed in this batch).

## Notes
- No fallback to `src` or legacy inline prose was introduced.
- Semantic authority remains in `scripts/skill_hub_cards_core.py`.
