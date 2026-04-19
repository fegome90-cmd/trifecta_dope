## Exploration: skill-hub-render-ux-recovery
### Current State
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill-hub` is the current user entrypoint, but it still prints the search output directly and then calls the legacy hidden-authority banner from `/Users/felipe_gonzalez/.local/bin/skill_hub_info_card.py` on interactive terminals.
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill_hub_cards_core.py` is the governed classifier/planner: it parses search output, normalizes hits, classifies `renderable_skill` vs `metadata_only` vs `unsupported`, and enforces exit codes `0/1/3/4`.
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/src/cli/skill_cards.py` is the real skill-card renderer. It owns rich/compact/plain rendering for already-approved cards, including the rich panel title/header, source badge, relevance, triggers, and path.
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/src/cli/error_cards.py` is the canonical fail-closed error surface. It already emits stable markers and is used elsewhere in governed CLI orchestration.
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/docs/contracts/SKILL_HUB_CARDS_GOVERNED_CONTRACT.md` makes the authority boundary explicit: governed helper owns classification/rendering, metadata-only results must not masquerade as skills, and legacy/parasitic surfaces are deprecated.
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/braindope.md` converges on the UX principle that passive banners are weak, auto-escalation is too slow, and helpful failure/suggestions are preferred.
- Legacy evidence in `/Users/felipe_gonzalez/.local/bin/skill-hub.bak-sh005` and `/Users/felipe_gonzalez/.local/bin/skill_hub_info_card.py` shows the old UX pattern: big banner, sentence-query guidance, and an interactive-terminal info card. That is comparison-only, not a runtime target.

### Affected Areas
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill-hub` — top-level orchestration is where the banner/guidance feel currently leaks through legacy home-bin code and where the public entrypoint should be made governed.
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill_hub_cards_core.py` — owns search→normalize→classify→render-plan authority; it is the right place to keep semantic decisions, not presentation-only hacks.
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/src/cli/skill_cards.py` — should stay focused on rendering approved skill cards; it can host a small governed intro/header helper if we want a reusable terminal banner.
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/src/cli/error_cards.py` — should carry the error-driven orchestration feel for empty/unsupported/precondition failures instead of shell-echoing ad hoc messages.
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/docs/contracts/SKILL_HUB_CARDS_GOVERNED_CONTRACT.md` — the contract needs to stay the SSOT for authority ownership while UX is recovered.
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/openspec/changes/skill-hub-render-ux-recovery/exploration.md` — exploration artifact only; no runtime authority.

### Approaches
1. **Light retrofit in the public shell wrapper**
   - Keep `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill-hub` as the composition point.
   - Replace the home-bin info card with repo-owned banner/guidance rendering and delegate all card classification/rendering to governed helpers.
   - Pros: smallest delta, preserves the old “entrypoint owns the first impression” behavior.
   - Cons: banner/guidance logic remains in shell orchestration, which is harder to test and easier to drift.
2. **Dedicated governed UX composer**
   - Add a small repo-owned module for banner + sentence-query guidance + non-renderable orchestration frames, then have `skill-hub` call it.
   - Keep `scripts/skill_hub_cards_core.py` as planner/classifier, `src/cli/skill_cards.py` as skill-card renderer, and `src/cli/error_cards.py` as failure surface.
   - Pros: clean authority split, easiest to test, no hidden-authority dependency.
   - Cons: one more module, slightly more plumbing.
3. **Fold guidance into the renderers**
   - Extend `src/cli/skill_cards.py` and `src/cli/error_cards.py` so the banner/guidance is emitted alongside the existing render paths.
   - Pros: fewer files.
   - Cons: mixes “what is a skill card” with “what should the user do next,” and risks muddying renderer responsibilities.

### Recommendation
Choose **Approach 2**. Recover the big banner and sentence-query guidance as a small governed UX composer, not as a hidden home-bin script and not as a renderer side effect. Let `skill_hub_cards_core.py` keep semantic authority, let `skill_cards.py` render approved skill cards, and let `error_cards.py` own the fail-closed orchestration frames. That restores the old feel while keeping the pipeline governed and testable.

### Risks
- The requested hybrid persistence cannot be fully honored in this parent runtime because Engram persistence is unavailable here; this exploration is therefore filesystem-only at `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/openspec/changes/skill-hub-render-ux-recovery/exploration.md`.
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill-hub` currently depends on `/Users/felipe_gonzalez/.local/bin/skill_hub_info_card.py`; removing it will change terminal UX, so the migration must be deliberate.
- `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill-hub-cards` in the repo is still a legacy helper shape, so the proposal must avoid treating it as the canonical runtime authority.
- Any recovery must preserve stdout/stderr separation and the governed exit-code contract (`0`, `1`, `3`, `4`) so pipes and automation do not break.

### Ready for Proposal
Yes — tell the user we found a clean governed path: recover the banner/guidance as repo-owned UX composition, keep classification/rendering authority inside the governed pipeline, and explicitly retire the hidden `/Users/felipe_gonzalez/.local/bin/*` surfaces from runtime behavior.
