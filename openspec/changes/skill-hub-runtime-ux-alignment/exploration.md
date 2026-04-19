## Exploration: skill-hub-runtime-ux-alignment

### Current State
The promoted runtime still only copies `scripts/skill-hub` and `scripts/skill-hub-cards`; it does **not** ship `src/`, and the previous gate confirmed that `python3 -c 'from src.cli.skill_cards import render_skill_hub_intro'` fails after promotion. In practice, `scripts/skill-hub` now tries to import `src.cli.skill_cards` / `src.cli.error_cards` and falls back to inline prose when those imports fail, so the promoted binary does not reliably use the governed intro/error surfaces. Separately, `scripts/skill-hub-cards` still owns its own stderr prose for parse/runtime failures and keeps non-renderable fallback paths in the wrapper instead of routing those failures through a governed error-card surface.

### Affected Areas
- `scripts/skill-hub-runtime` — promotion boundary proves what ships; today it excludes `src/`, which is why runtime imports fail after promotion.
- `scripts/skill-hub` — first-impression intro and empty-query error path still depend on `src.cli.*` with inline fallback prose.
- `scripts/skill-hub-cards` — wrapper still emits raw stderr prose for parse/runtime failures and maintains legacy fallback handling.
- `scripts/skill_hub_cards_core.py` — already the governed classifier/render-plan authority; likely the best promoted home for runtime-owned UX helpers.
- `src/cli/skill_cards.py` — canonical intro/card presentation helper exists here, but it is not available in promoted runtime binaries.
- `src/cli/error_cards.py` — canonical structured error-card renderer exists here, but it is likewise not shipped into the promoted runtime.
- `tests/unit/test_skill_hub_runtime_promotion.py` — current gate evidence pins the source-unavailable failure mode after promotion.
- `tests/unit/test_skill_hub_cards_wrapper_contract.py` — current contract coverage shows the wrapper is expected to keep stdout/stderr separation and governed error framing.

### Approaches
1. **Promote a runtime-owned UX facade under `scripts/`** — add a tiny shared helper module for intro + error framing, then have both entrypoints import it.
   - Pros: Works in promoted binaries, removes hidden `src` authority, smallest change that fixes both findings.
   - Cons: Duplicates thin presentation wrappers outside `src`; requires updating promotion/tests for one more script file if split out.
   - Effort: Low

2. **Move the governed intro/error helpers into `scripts/skill_hub_cards_core.py`** — keep all promoted runtime framing in the already-shipped governed core.
   - Pros: No new runtime module; keeps runtime authority in one promoted place; still avoids `src` dependency.
   - Cons: Mixes presentation framing with classifier/render-plan logic; the file gets broader and less clean.
   - Effort: Low

3. **Expand promotion to include `src/cli/*`** — make promoted runtime ship the canonical helpers directly.
   - Pros: Reuses the exact canonical implementations from `src`.
   - Cons: Bigger promoted surface, more hidden authority risk, and it is not the smallest fix; also changes the runtime contract rather than aligning to it.
   - Effort: Medium/High

### Recommendation
Use **Approach 1**, with the shared runtime facade living in `scripts/` and being the only promoted dependency for `skill-hub` / `skill-hub-cards`. That keeps the governed intro and fail-closed error framing available after promotion, removes the `src` availability problem, and avoids reintroducing hidden authority. If you want to minimize file count even further, fold that facade into `scripts/skill_hub_cards_core.py`, but the architectural principle stays the same: promoted runtime UX must live in promoted runtime code.

### Risks
- The current hybrid persistence model is asymmetric: Engram is unavailable in this parent runtime, so this exploration only persists on filesystem; if the filesystem artifact is lost, the phase context is gone.
- If the fix stays in `src.cli.*`, promoted binaries will continue to fall back to raw prose because `src` is not shipped.
- If fail-closed framing remains split between wrapper and helper, stderr semantics can drift again and the governed error cards will lose authority.
- Expanding promotion to `src/` would solve the import failure but broadens the runtime surface and risks hidden authority creeping back in.

### Ready for Proposal
Yes — tell the user the runtime-owned intro/error helpers need to move into promoted `scripts/` code (or an adjacent promoted facade) so the promoted binary can keep governed UX without depending on `src`.
