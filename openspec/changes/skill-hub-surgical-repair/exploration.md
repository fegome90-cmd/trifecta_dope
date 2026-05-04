## Exploration: skill-hub-surgical-repair

### Current State
`skill-hub` is now a promoted runtime wrapper around the `skills-hub` segment. Its alias rerank path asks `trifecta ctx search --explain --explain-format json`, reads `expansions.expanded_terms`, then only recognizes canonical hits whose refs start with `repo:{term}.md:`. That misses the live segment shape `skill:{name}:...`, so a real skill hit can fail to produce the intended `Canonical alias match:` block even when the explain payload already contains the evidence.

The query linter is global, not segment-aware. For any vague query with `token_count <= 2`, `src/domain/query_linter.py` injects `agent.md` and `prime.md` as default strong anchors from `configs/anchors.yaml`. That makes sense for legacy context-pack search, but it is actively wrong for the `skills-hub` segment, where tests already assert that legacy context singletons like `prime.md` are not indexed and where vague skill searches should not be pulled toward `_ctx` entrypoints.

Card authority is currently split. `scripts/skill_hub_cards_core.py` owns the governed runtime plan with `RawSearchHit`, `NormalizedResult`, `ClassifiedResult`, `SkillCard`, `RenderPlan`, exit codes, parsing, normalization, classification, `render_plain`, `render_rich`, and `_select_renderer`. Separately, `src/application/skill_card_view_model.py` defines `SkillCardViewModel` as the canonical renderer boundary, and tests under `test_skill_hub_render_parity.py`, `test_skill_hub_cards_adapter.py`, and `test_skill_hub_renderer_handover.py` import `SkillCardViewModel` and `build_view_model` from `scripts.skill_hub_cards_core`. The current `scripts/skill_hub_cards_core.py` inspected here does not define either symbol and `NormalizedResult` has no `authority_state`, so the tests and governed runtime core are describing competing contracts.

Intro/banner authority is also duplicated. The promoted runtime ships `scripts/skill_hub_runtime_ux.py`, where `SKILL_HUB_INTRO_BANNER` is `=== Skill Hub ===` and rich TTY mode can render the ASCII hero. `src/cli/skill_cards.py` has a reference-only `_SKILL_HUB_INTRO_BANNER` with the same simple banner. Promotion tests assert the wrapper itself must not inline the intro copy, while runtime UX tests expect the simple banner. If the intended contract is now rich hero on TTY and simple banner otherwise, tests need to pin that split; if the intended contract is only the simple banner, the hero is unused surface area.

Runtime promotion is governed by `scripts/skill-hub-runtime`: it copies and verifies `scripts/skill-hub`, `scripts/skill-hub-cards`, `scripts/skill_hub_runtime_ux.py`, and `scripts/skill_hub_cards_core.py` via schema version 2 receipts and SHA checks. That is the right authority for resolving broken registered runtime entries. Manual edits to a manifest or promoted target would be evidence drift, not authority; the repair should change governed sources and use `skill-hub-runtime promote/verify` in the proposal/apply phases.

Engram mem_* tools were not exposed in this session, so no Engram save was performed; this exploration is persisted only to the requested openspec artifact.

### Affected Areas
- `scripts/skill-hub` — alias canonical rerank currently matches only `repo:{name}.md:` refs and should recognize live `skill:{name}:` refs without broadening to arbitrary refs.
- `src/domain/query_linter.py` — owns vague-query default expansion and currently injects `agent.md` / `prime.md` without knowing the active segment.
- `configs/anchors.yaml` — contains `agent.md` and `prime.md` as global strong file anchors; repair should avoid mutating global anchors just to satisfy `skills-hub` behavior.
- `scripts/skill_hub_cards_core.py` — governed runtime classifier/render-plan authority; currently lacks the `SkillCardViewModel`, `build_view_model`, and `authority_state` contract expected by related tests.
- `src/application/skill_card_view_model.py` — competing canonical view-model authority for renderers; must either become the single model imported by runtime code or remain repo-side only while runtime owns its own explicit contract.
- `src/cli/skill_cards.py` — repo-side renderer consumes `SkillCardViewModel` and duplicates intro constants; useful reference, but not shipped by the promoted runtime.
- `scripts/skill_hub_runtime_ux.py` — promoted runtime UX authority for intro/banner and runtime card rendering; must align with tests and card contract.
- `scripts/skill-hub-runtime` — governed promote/verify authority for runtime artifacts; use this to resolve broken registered entries instead of editing promoted targets or receipts by hand.
- `tests/unit/test_skill_hub_runtime_promotion.py` — pins promotion boundary, wrapper dependency rules, receipt schema, and simple intro/guidance behavior after promotion.
- `tests/unit/test_skill_hub_render_parity.py` — currently assumes `scripts.skill_hub_cards_core` exposes `SkillCardViewModel`, `build_view_model`, and `authority_state`; this is direct evidence of card-contract drift.
- `tests/unit/test_skill_hub_cards_adapter.py` — expects a classified-result-to-view-model adapter and strict `healthy` / `degraded` fallback behavior.
- `tests/unit/test_skill_hub_renderer_handover.py` — expects `_select_renderer` to hand renderable cards to the new view-model renderer path, including compact style.
- `openspec/changes/skill-hub-runtime-ux-alignment/*` — previous change established promoted `scripts/` UX facades because `src` is unavailable after promotion.
- `openspec/changes/skill-hub-render-ux-recovery/*` — previous exploration/design recommended repo-governed UX composition and retiring hidden home-bin surfaces.

### Approaches
1. **Surgical compatibility repair in governed runtime core** — Extend existing runtime contracts minimally: support both `repo:{name}.md:` and `skill:{name}:` alias refs in `scripts/skill-hub`; add an optional segment/lint profile so `skills-hub` disables vague default entrypoint injection; make `scripts/skill_hub_cards_core.py` expose the view-model adapter contract expected by tests while using one imported/shared `SkillCardViewModel` model; pin intro behavior in runtime UX tests; resolve registration by running governed promote/verify.
   - Pros: Smallest change set, respects promoted runtime boundary, preserves existing exit codes and wrapper contract, and directly addresses the observed drifts.
   - Cons: Keeps some compatibility shims in `scripts/skill_hub_cards_core.py`; requires careful import strategy because promoted runtime cannot depend on the full `src` package unless promotion expands.
   - Effort: Medium

2. **Runtime-owned cards contract only** — Declare `scripts/skill_hub_cards_core.py` / `scripts/skill_hub_runtime_ux.py` as the single promoted card authority, remove or rewrite tests that import `SkillCardViewModel` from runtime core, and keep `src/application/SkillCardViewModel` as repo-side/deprecated reference only.
   - Pros: Cleanest promoted-runtime boundary; no hidden `src` dependency; aligns with prior openspec findings that runtime must live under promoted `scripts/` code.
   - Cons: Requires updating several tests that already encode the view-model handover; risks leaving repo-side renderers and runtime renderers divergent unless deprecation is explicit.
   - Effort: Medium

3. **Repo-wide `SkillCardViewModel` as SSOT, promote its dependencies** — Make `src/application/skill_card_view_model.py` the single card authority and expand `skill-hub-runtime` promotion to ship the minimal `src/application` / `src/cli` modules needed by runtime rendering.
   - Pros: One dataclass/model across repo and runtime; tests that import/use `SkillCardViewModel` can stay conceptually valid.
   - Cons: Broadens the promoted surface, conflicts with prior runtime-UX alignment evidence that `src` is not shipped, increases receipt complexity, and risks reintroducing hidden authority by promoting partial `src` slices.
   - Effort: High

4. **Manual promoted-entry cleanup only** — Fix broken registered entries by editing manifests/receipts/promoted targets directly and leave code contracts mostly unchanged.
   - Pros: Fast apparent recovery for one machine.
   - Cons: Violates the governed tooling contract, creates evidence/authority drift, does not fix alias or linter root causes, and will regress on the next promotion.
   - Effort: Low initially, High operationally

### Recommendation
Use Approach 1 with one strict architectural rule: **one surface, one authority**. Keep runtime behavior governed by promoted `scripts/` artifacts, but do not let `SkillCard` and `SkillCardViewModel` compete silently. The least risky repair is to make `scripts/skill_hub_cards_core.py` the adapter boundary: it can produce one canonical runtime view model for rendering, normalize `authority_state`, and keep `RenderPlan.cards` / `classified_results` coherent. If implementation discovers that importing `src.application.SkillCardViewModel` is unsafe in promoted runtime, define the runtime-owned model in `scripts/` and update tests to import that authority explicitly; do not keep both as equal SSOTs.

For alias matching, change only the canonical-match predicate to accept exact live IDs (`skill:{term}:` or the actual live ref shape confirmed by tests) alongside legacy `repo:{term}.md:`. Do not loosen it to substring matching, because that would make alias promotion noisy.

For the query linter, prefer a segment-aware option over removing `agent.md` / `prime.md` from `configs/anchors.yaml`. Those anchors still belong to context-pack use cases. `skills-hub` should pass a lint profile/segment hint that disables vague default entrypoint boosts while preserving alias/doc boosts.

For intro/banner, decide and pin the contract rather than chasing tests. The likely contract from inspected code is: simple `=== Skill Hub ===` for non-TTY/plain output, optional ASCII hero for rich TTY output, always followed by sentence-query guidance. If that is intended, update/add tests accordingly; if not, remove the unused hero from `scripts/skill_hub_runtime_ux.py`.

For broken registered entries, repair governed source and then use `scripts/skill-hub-runtime promote` and `verify` as the only authority path in apply/verification. Receipts and promoted targets should remain evidence of governed artifacts, not hand-edited configuration.

### Risks
- Tests currently import symbols that do not exist in the inspected `scripts/skill_hub_cards_core.py`; implementation may need to choose between adding compatibility exports or correcting tests to the true promoted authority.
- Segment-aware linting can leak complexity into a pure domain function if implemented with environment checks; prefer explicit parameters or caller-owned profile selection.
- Supporting `skill:{name}:` alias refs must stay exact; loose matching can create false canonical matches for unrelated skills.
- Expanding promotion to include `src` would solve imports but increases the runtime authority surface and contradicts previous runtime-boundary findings.
- Intro/banner changes are user-visible; changing from simple banner to rich hero by default can break snapshot-like tests or scripted output expectations.
- Manual manifest or receipt edits may appear to fix a broken local registration but will be overwritten by governed promotion and should be rejected.

### Ready for Proposal
Yes — tell the user the proposal should be a surgical governed-runtime repair: exact live skill-ref alias matching, segment-aware linter defaults for `skills-hub`, one explicit card view-model authority, pinned intro/banner behavior, and registration recovery only through `skill-hub-runtime promote/verify`.

- status: completed
- executive_summary: Explored `skill-hub-surgical-repair` and found five connected contract drifts: legacy-only alias refs, global vague-query injection unsuitable for `skills-hub`, split card authorities, duplicated intro/banner expectations, and registration recovery that must stay governed by promotion receipts.
- artifacts: `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/openspec/changes/skill-hub-surgical-repair/exploration.md`
- next_recommended: Create proposal/spec/design for the surgical repair, then implement with tests focused on alias ref shapes, segment-aware linting, card authority, intro/banner contract, and runtime promote/verify flow.
- risks: Card-contract tests and runtime core currently disagree; segment-aware linting must avoid environment-coupled domain logic; promoted runtime must not silently depend on unshipped `src`; registration must not be repaired by hand-editing receipts or targets.
- skill_resolution: injected
