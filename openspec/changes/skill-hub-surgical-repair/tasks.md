# Tasks: Skill Hub Surgical Repair

## Phase 1: Linter Segment + Profile Awareness

- [x] 1.1 RED: `test_expand_query_skills_hub_excludes_defaults` in `tests/unit/test_query_linter.py` — assert `added_strong` excludes `agent.md`/`prime.md` when `segment="skills-hub"`, token_count=1 — **AUTH-004**
- [x] 1.2 RED: `test_expand_query_default_segment_retains_defaults` — assert `added_strong` contains `agent.md`/`prime.md` when `segment=None` — **AUTH-005**
- [x] 1.3 RED: `test_expand_query_profile_overrides_segment` — assert `added_strong` excludes defaults when `lint_profile={"disable_entrypoint_anchors": True}`, regardless of segment — **AUTH-006**
- [x] 1.4 RED: `test_expand_query_regression_existing_behavior` — assert existing lint output unchanged when neither segment nor profile is passed — **AUTH-005** (baseline)
- [x] 1.5 GREEN: Add `segment: str | None = None` + `lint_profile: dict | None = None` to `expand_query()` in `src/domain/query_linter.py`. Guard default-injection block with: `disable_entrypoint_anchors = bool(lint_profile and lint_profile.get("disable_entrypoint_anchors"))` then `if segment != "skills-hub" and not disable_entrypoint_anchors:` — note the None-safe guard, `lint_profile=None` must not raise
- [x] 1.6 RED: `test_lint_query_propagates_segment_and_profile` — call `lint_query(..., segment="skills-hub")` and `lint_query(..., lint_profile={"disable_entrypoint_anchors": True})`, verify expanded query has no entrypoint anchors — **AUTH-004**, **AUTH-006**
- [x] 1.7 GREEN: Propagate `segment` + `lint_profile` kwargs through `lint_query()` → `expand_query()` call
- [x] 1.8 RED: `test_cli_segment_env_var_forwarded` — set `TRIFECTA_SEGMENT=skills-hub` env var, call search use case, verify `lint_query` receives `segment="skills-hub"` — **AUTH-004**
- [x] 1.9 GREEN: Read `TRIFECTA_SEGMENT` env var in `src/infrastructure/cli.py` (ctx search command), pass to `SearchUseCase`; forward `segment` through `search_get_usecases.py` → `lint_query()`
- [x] 1.10 GREEN: Set `TRIFECTA_SEGMENT=skills-hub` in `scripts/skill-hub` before calling `trifecta ctx search`

## Phase 2: Dual-Family Alias Matching

- [x] 2.1 RED: `test_alias_match_skill_ref` in `tests/unit/test_skill_hub_alias.py` — feed explain JSON with `skill:python-patterns:` ref, assert canonical match produced — **AUTH-001**
- [x] 2.2 RED: `test_alias_match_legacy_ref` — feed `repo:python-patterns.md:` ref, assert still matched — **AUTH-002**
- [x] 2.3 RED: `test_alias_match_rejects_substring` — feed `skill:python-patterns-extra:`, assert no match for query `python-patterns` — **AUTH-003**
- [x] 2.4 GREEN: In `scripts/skill-hub` inline Python, add `skill_prefix = f"skill:{term}:"` and check `ref.startswith(skill_prefix)` alongside existing `repo_prefix` check

## Phase 3: Card Adapter + View Model + Renderer Handoff

- [x] 3.0 DELETE + REWRITE: Delete existing `tests/unit/test_skill_hub_cards_adapter.py` and rewrite from scratch.
- [x] 3.1 RED: `test_classify_result_sets_authority_state_healthy` — **UX-001**
- [x] 3.2 RED: `test_classify_result_sets_authority_state_degraded` — **UX-002**
- [x] 3.3 GREEN: Extend `ClassifiedResult` with `authority_state`, modify `classify_result()` for degraded path
- [x] 3.3b GREEN: Add `fidelity_level` and `compact_flag` to `RuntimeSkillCard`
- [x] 3.4 RED: `test_build_view_model_healthy` — **UX-001**
- [x] 3.5 RED: `test_build_view_model_degraded_partial` — **UX-002**
- [x] 3.5b RED: `test_build_view_model_returns_none_for_non_renderable` — **UX-003**
- [x] 3.5c RED: `test_build_view_model_degraded_minimal` — **UX-002**
- [x] 3.6 GREEN: Add `build_view_model()` adapter
- [x] 3.7 GREEN: Skip — no current consumers of SkillCardViewModel alias
- [x] 3.8 RED: `test_select_renderer_routes_to_plain` — **UX-004**
- [x] 3.9 RED: `test_select_renderer_routes_to_rich` — **UX-005**
- [x] 3.10 GREEN: Extend `_select_renderer()` with `is_tty` + `cards_vm` routing

## Phase 4: Intro/Banner Pinning (Characterization Tests)

- [x] 4.1 GREEN: `test_render_intro_plain` — **UX-006**
- [x] 4.2 GREEN: `test_render_intro_rich` — **UX-007**
- [x] 4.3 GREEN: `test_render_intro_only_two_variants` — **UX-008**

## Phase 5: Operational Registration Recovery

- [x] 5.1 Run `scripts/skill-hub-runtime verify` to identify broken entries — operational, run locally
- [x] 5.2 Run `scripts/skill-hub-runtime promote` from governed source to repair — **AUTH-007** — operational, run locally
- [x] 5.3 Run `scripts/skill-hub-runtime verify` again — assert PASS — operational, run locally
- [x] 5.4 GREEN: `test_verify_detects_manual_edits` in `tests/unit/test_skill_hub_runtime_promotion.py` — already covered by `test_verify_fails_closed_when_promoted_target_drifts` (line 223) — **AUTH-008**

## Coverage Matrix

| Scenario ID | Description | Tasks |
|-------------|-------------|-------|
| AUTH-001 | Live skill ref matched | 2.1, 2.4 |
| AUTH-002 | Legacy ref still matched | 2.2, 2.4 |
| AUTH-003 | Substring ref rejected | 2.3, 2.4 |
| AUTH-004 | skills-hub segment excludes anchors | 1.1, 1.6, 1.8, 1.9, 1.10 |
| AUTH-005 | Default segment retains anchors | 1.2, 1.4 |
| AUTH-006 | Explicit profile overrides segment | 1.3, 1.6 |
| AUTH-007 | Promote repairs registration | 5.1, 5.2, 5.3 |
| AUTH-008 | Manual edit rejected | 5.4 |
| UX-001 | Card adapter produces view model (healthy) | 3.0, 3.1, 3.4, 3.6 |
| UX-002 | Degraded fallback | 3.0, 3.2, 3.5, 3.6 |
| UX-003 | Non-renderable produces None | 3.5b, 3.6 |
| UX-004 | Plain renderer handoff | 3.8, 3.10 |
| UX-005 | Rich renderer handoff | 3.9, 3.10 |
| UX-006 | Plain intro output | 4.1 |
| UX-007 | Rich intro output | 4.2 |
| UX-008 | No other intro variants | 4.3 |
