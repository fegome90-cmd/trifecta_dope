# Tasks: skill-hub-render-ux-recovery

## Phase 1 — **$superpowers:test-driven-development** + **$authority-flow-audit**
- [x] Add/adjust tests first in `tests/unit/test_skill_hub_cards_governed.py`, `tests/unit/test_skill_hub_cards_wrapper_contract.py`, and `tests/unit/test_skill_hub_runtime_promotion.py`.
- [x] Cover governed intro/banner rendering, sentence-query guidance, stdout/stderr separation, fail-closed exit codes, and “no `~/.local/bin` authority” behavior.
- [x] Use `docs/contracts/SKILL_HUB_CARDS_GOVERNED_CONTRACT.md` plus `bangen_dope/README.md` only as presentation inspiration/reference, never as runtime authority.

## Phase 2 — **$python-cli-patterns** + **$cli-developer** + **$typeui-design-systems/typeui-bold**
- [x] Implement a repo-owned intro composer in `src/cli/skill_cards.py` that renders the banner/guidance text cleanly for terminal output.
- [x] Add governed error framing in `src/cli/error_cards.py` so unsupported/empty/malformed states can emit structured cards without shell `echo`.
- [x] Update `scripts/skill-hub` to call the repo-owned intro path, remove the `~/.local/bin/skill_hub_info_card.py` runtime call, and keep the current exit-code contract intact.
- [x] Keep `scripts/skill_hub_cards_core.py` as the classifier/render-plan authority; do not move semantic logic into the wrapper.

## Phase 3 — **$authority-flow-audit** + docs sync
- [x] Re-run and tighten tests against the modified paths above, especially the wrapper contract and governed render tests.
- [x] Update `docs/contracts/SKILL_HUB_CARDS_GOVERNED_CONTRACT.md` so it explicitly states intro/guidance is presentation-only and legacy home-bin helpers are comparison-only, not canonical runtime.
- [x] Verify the new file/flow boundaries still match the design intent in `openspec/changes/skill-hub-render-ux-recovery/design.md`.

## Phase 4 — **$/Users/felipe_gonzalez/.config/opencode/skills/sdd-gate-skill** + fallback **$superpowers:verification-before-completion** + **$branch-review**
- Run the pre-implementation/final quality gate with `/Users/felipe_gonzalez/.config/opencode/skills/sdd-gate-skill` against spec, design, and tasks completeness before declaring the change ready to apply/close.
- Then perform the evidence-based completion gate: confirm the intro renders, stderr carries governed error cards, success/failure exit codes remain unchanged, and no hidden-authority `~/.local/bin` surface is referenced in runtime code paths.
- If the dedicated SDD gate is unavailable in the executor environment, fall back to `verification-before-completion` plus `branch-review`; record only verifiable outcomes and stop on ambiguity.
