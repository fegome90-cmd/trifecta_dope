# Apply Progress — skill-hub-default-path-origin-doctor

## Scope applied
Implemented within owned scope only.

## Files touched
### Runtime / wrappers
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill-hub`
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill-hub-cards`
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill-hub-runtime`
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill_hub_runtime_ux.py`
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill_hub_cards_core.py`

### Tests
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/tests/unit/test_skill_hub_runtime_promotion.py`
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/tests/unit/test_skill_hub_cards_wrapper_contract.py`
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/tests/unit/test_skill_hub_render_parity.py` (validated in focused slice)
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/tests/unit/test_skill_hub_cards_governed.py` (validated in focused slice)

### Openspec artifacts
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/openspec/changes/skill-hub-default-path-origin-doctor/tasks.md`
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/openspec/changes/skill-hub-default-path-origin-doctor/apply-progress.md`

## Commands run
1. Initial focused verify after edits:
```bash
uv run pytest -q \
  tests/unit/test_skill_hub_cards_wrapper_contract.py \
  tests/unit/test_skill_hub_runtime_promotion.py \
  tests/unit/test_skill_hub_cards_governed.py \
  tests/unit/test_skill_hub_render_parity.py
```
- Result: failed during iteration; assertions/contracts updated accordingly.

2. Final focused verification slice:
```bash
uv run pytest -q \
  tests/unit/test_skill_hub_cards_wrapper_contract.py \
  tests/unit/test_skill_hub_runtime_promotion.py \
  tests/unit/test_skill_hub_cards_governed.py \
  tests/unit/test_skill_hub_render_parity.py
```
- Exact result: `52 passed in 2.12s`

3. Phase 5 closure rerun after adding promoted-runtime proof test:
```bash
uv run pytest -q \
  tests/unit/test_skill_hub_cards_wrapper_contract.py \
  tests/unit/test_skill_hub_runtime_promotion.py \
  tests/unit/test_skill_hub_cards_governed.py \
  tests/unit/test_skill_hub_render_parity.py
```
- Exact result: `53 passed in 3.04s`

## Contract outcomes implemented
- `--cards` admission is now order-independent in `skill-hub` wrapper.
- Default path now emits governed intro/render via runtime UX before search output.
- `skill-hub-cards` wrapper preserves downstream exit codes (no forced `1` remap).
- Canonical runtime artifact map in `skill-hub-runtime` now includes:
  - `skill-hub`
  - `skill-hub-cards`
  - `skill_hub_runtime_ux.py`
  - `skill_hub_cards_core.py`
  and is shared by both `promote` and `verify`.
- `skill_hub_runtime_ux.py` owns presentation intro/error/card formatting surfaces; `skill_hub_cards_core.py` remains semantic authority.

## Strict-TDD cycle evidence (Phase 5 closure)

| Cycle | Evidence | Result |
|---|---|---|
| RED (contract gap) | Existing verify artifact flagged promoted default-path intro scenario as `UNTESTED` in `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/openspec/changes/skill-hub-default-path-origin-doctor/verify-report.md` | Failing closure condition existed before code/test update |
| GREEN (new proof added) | Added `test_promoted_runtime_default_path_keeps_governed_intro_and_sentence_guidance` in `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/tests/unit/test_skill_hub_runtime_promotion.py` and ran: `uv run pytest -q tests/unit/test_skill_hub_cards_wrapper_contract.py tests/unit/test_skill_hub_runtime_promotion.py tests/unit/test_skill_hub_cards_governed.py tests/unit/test_skill_hub_render_parity.py` | `53 passed in 3.04s` |
| REFACTOR/guard | Re-ran authority-focused rerun slice: `uv run pytest -q tests/unit/test_skill_hub_runtime_promotion.py -k "test_wrapper_chain_uses_only_governed_runtime_dependencies or test_promote_generates_targets_and_governed_receipt_schema_v2 or test_verify_fails_closed_when_receipt_set_mismatches_governed_contract or test_promoted_runtime_default_path_keeps_governed_intro_and_sentence_guidance"` | `4 passed, 12 deselected in 0.43s` |

## Warnings / remaining items
- `tasks.md` item **1.2** remains open: no dedicated acceptance-test file was added/updated in `tests/acceptance/`; coverage was implemented in focused unit wrapper contract tests instead.
- `tasks.md` item **4.3** is now closed by explicit artifact: `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/openspec/changes/skill-hub-default-path-origin-doctor/gate-rerun.md`.
