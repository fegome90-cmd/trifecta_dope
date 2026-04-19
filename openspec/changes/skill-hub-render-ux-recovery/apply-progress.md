# Apply Progress: skill-hub-render-ux-recovery

- Date: 2026-04-17
- Status: launching sdd-apply sequential subagents
- Note: Engram persistence unavailable in this runtime; this local file is the compaction fallback.
- Next: Phase 2 implementation (repo-owned intro composer + wrapper orchestration updates).

## 2026-04-18 — Worker 1 (Phase 1 / RED pinning)

- Added RED contract tests in:
  - `tests/unit/test_skill_hub_cards_governed.py`
  - `tests/unit/test_skill_hub_cards_wrapper_contract.py`
  - `tests/unit/test_skill_hub_runtime_promotion.py`
- New assertions pin governed UX requirements: intro/banner rendering, sentence-query guidance, stream separation (stdout vs stderr), fail-closed non-zero exits, and explicit prohibition of `~/.local/bin` runtime authority.
- Validation run: `uv run pytest tests/unit/test_skill_hub_cards_governed.py tests/unit/test_skill_hub_cards_wrapper_contract.py tests/unit/test_skill_hub_runtime_promotion.py -q`
  - Result: failing (RED by intent) until Phase 2 production implementation lands.

## 2026-04-18 — Worker 2 (Phase 2 / GREEN implementation)

- Implemented repo-owned intro composer in `src/cli/skill_cards.py`:
  - Added `render_skill_hub_intro(query_hint=..., file=...)` with governed banner + sentence-query guidance.
- Implemented governed error framing in `src/cli/error_cards.py`:
  - Added `emit_skill_hub_error_card(...)` to write structured `TRIFECTA_ERROR_CODE` cards to stderr.
- Updated `scripts/skill-hub` orchestration:
  - Added `--cards` execution path that prints governed intro and delegates to adjacent `skill-hub-cards`.
  - Removed runtime dependency on `~/.local/bin/skill_hub_info_card.py`.
  - Preserved fail-closed behavior by propagating helper exit codes unchanged and using governed error cards for empty-query validation failures.
- Kept semantic authority in `scripts/skill_hub_cards_core.py`:
  - Classification/normalization logic unchanged.
  - Adjusted `render_plain`/`render_rich` to render real skill cards for `renderable_skill` outcomes while keeping non-renderable messaging paths intact.

- Focused verification:
  - `uv run pytest -q tests/unit/test_skill_hub_cards_governed.py::test_query_with_skill_result_renders_card_and_exit_zero tests/unit/test_skill_hub_cards_governed.py::test_plain_and_rich_render_share_same_classification tests/unit/test_skill_hub_cards_governed.py::test_skill_cards_module_exposes_governed_intro_renderer tests/unit/test_skill_hub_cards_governed.py::test_governed_intro_renderer_emits_sentence_query_guidance tests/unit/test_skill_hub_cards_wrapper_contract.py tests/unit/test_skill_hub_runtime_promotion.py::test_wrapper_chain_uses_only_governed_runtime_dependencies tests/unit/test_skill_hub_runtime_promotion.py::test_promote_generates_targets_and_governed_receipt_schema_v2`
    - Result: pass (10 passed)
  - `uv run pytest -q tests/unit/test_skill_hub_cards_governed.py tests/unit/test_skill_hub_cards_wrapper_contract.py tests/unit/test_skill_hub_runtime_promotion.py`
    - Result: 28 passed, 3 failed (all failures isolated to `scripts/skill-hub-cards` CLI flags not in Worker 2 ownership scope).

## 2026-04-18 — Worker 3 (Phase 3 / wrapper flags + docs sync)

- Fixed remaining `scripts/skill-hub-cards` CLI contract gaps:
  - Added governed flags `--style {plain,rich}` and `--stdin-search-output`.
  - Made `query` optional only when `--stdin-search-output` is used (otherwise fail-closed with non-zero).
  - Added strict stdin JSON validation for parse failures (`parse error`) and invalid `hits` shape (`invalid hits list`) with exit code `1`.
- Synced contract documentation:
  - Updated `docs/contracts/SKILL_HUB_CARDS_GOVERNED_CONTRACT.md` to state intro/banner/guidance are presentation-only UX framing.
  - Added explicit policy that `~/.local/bin` legacy helpers are comparison-only references, never canonical runtime authority.
- Phase 3 boundary check:
  - Verified wrapper/runtime authority constraints remain aligned with design intent (governed runtime surfaces stay `scripts/skill-hub` + `scripts/skill-hub-cards`; no home-bin authority dependency introduced).
- Focused verification:
  - `uv run pytest -q tests/unit/test_skill_hub_cards_governed.py tests/unit/test_skill_hub_cards_wrapper_contract.py tests/unit/test_skill_hub_runtime_promotion.py`
    - Result: **31 passed, 0 failed**.


## 2026-04-18 — Worker 4 (Phase 4 / sequential gate)

- Ran focused verification exactly as requested:
  - `uv run pytest -q tests/unit/test_skill_hub_cards_governed.py tests/unit/test_skill_hub_cards_wrapper_contract.py tests/unit/test_skill_hub_runtime_promotion.py`
  - Result: **31 passed in 0.95s**.
- Sequential gate lenses executed against spec/design/tasks plus current runtime implementation.
- Gate result: **REVIEW** (not PASS), so Phase 4 checklist was **not** marked complete.
- Key findings:
  - **HIGH**: promoted runtime intro falls back to inline wrapper text instead of the governed `src/cli/skill_cards.py` composer because promotion ships only `scripts/skill-hub` + `scripts/skill-hub-cards`.
  - **HIGH**: `scripts/skill-hub-cards` still emits raw stderr prose for runtime/parse failures and maintains its own parsing/rendering path instead of routing failures through governed error cards / the core classifier authority described in the design.
- Additional evidence check from isolated promoted runtime:
  - `python3 scripts/skill-hub-runtime promote --runtime-bin-dir <tmp>/bin --receipt-path <tmp>/receipt.json --repo-root .`
  - In the promoted directory, `python3 -c 'from src.cli.skill_cards import render_skill_hub_intro'` failed with `ModuleNotFoundError: No module named 'src'`, while `bin/skill-hub --cards "find testing"` still printed the intro banner via wrapper fallback text.
