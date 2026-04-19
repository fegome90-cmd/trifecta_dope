# Proposal: skill-hub rich runtime renderer

## Intent
Recover the beautiful rich skill-card rendering inside the governed promoted runtime so real `skill-hub` usage in TTY gets the intended visual hierarchy, not only the banner hero plus plain cards.

## Scope
### In Scope
- Add a governed rich runtime renderer for skill cards under `scripts/`.
- Preserve `skill_hub_cards_core.py` as semantic authority for admission, classification, and exit codes.
- Keep `plain` output for non-TTY / pipe / agent flows.
- Reuse visual intent from existing repo-side renderers and type-driven CLI aesthetics without making `src/cli/*` a promoted runtime dependency.
- Extend promotion/verification coverage if new runtime-owned artifacts are needed.

### Out of Scope
- Search ranking changes.
- New metadata semantics.
- Reintroducing runtime dependency on `src/cli/skill_cards.py` or other repo-side reference modules.
- Reworking intro/banner or error-card ownership again unless required by the renderer integration.

## Capabilities
### New Capabilities
- None.

### Modified Capabilities
- `skill-hub-authority`: presentation behavior in TTY mode will expand from plain cards to governed rich cards while preserving semantic authority boundaries.

## Approach
Treat this as a presentation-authority extension, not a semantic rewrite:
1. Keep one semantic pipeline in `scripts/skill_hub_cards_core.py`.
2. Introduce runtime-owned rich card rendering in governed `scripts/` code.
3. Route style by execution context:
   - TTY → rich renderer
   - non-TTY / pipes / agent flows → plain renderer
4. Preserve fail-closed behavior and promotion completeness for any runtime artifacts added or expanded.
5. Use the current repo-side renderers and type-oriented terminal design as reference only, not as runtime imports.

## Affected Areas
| Area | Impact | Description |
|------|--------|-------------|
| `scripts/skill_hub_runtime_ux.py` | Likely Modified | Add governed rich renderer and TTY-aware presentation routing. |
| `scripts/skill_hub_cards_core.py` | Likely Modified | Select runtime presentation mode while preserving semantic authority and exit codes. |
| `scripts/skill-hub-cards` | Possibly Modified | Keep runtime adapter aligned if renderer entry contract changes. |
| `scripts/skill-hub-runtime` | Possibly Modified | Ensure promotion/verify remains complete if runtime renderer surface expands. |
| `tests/unit/test_skill_hub_cards_governed.py` | Likely Modified | Cover governed card rendering behavior. |
| `tests/unit/test_skill_hub_render_parity.py` | Likely Modified | Reconcile parity expectations between runtime renderer and repo-side reference intent. |
| `tests/unit/test_skill_hub_runtime_promotion.py` | Likely Modified | Assert promoted runtime completeness for the governed renderer surface. |
| `tests/unit/test_skill_hub_runtime_ux.py` | Likely Modified | Validate TTY/plain governed renderer helpers and hero/runtime card presentation behavior. |

## Risks
| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Rich renderer accidentally takes semantic ownership | Med | Keep all admission/classification/exit logic in `skill_hub_cards_core.py` only. |
| Runtime re-couples to `src/cli/*` | Med | Treat repo-side renderers as reference-only and test for forbidden imports. |
| TTY-only heuristics create inconsistent output contracts | Med | Specify rich vs plain routing explicitly and test both paths. |
| Rich dependencies fail in promoted runtime | Low/Med | Keep runtime renderer self-contained and fail closed if required modules are unavailable. |

## Rollback Plan
If the rich runtime renderer regresses the CLI contract, revert runtime rendering selection to governed plain output while preserving the current banner, intro, promotion receipt, and semantic pipeline.

## Dependencies
- Existing governed runtime UX surface under `scripts/skill_hub_runtime_ux.py`
- Existing semantic authority in `scripts/skill_hub_cards_core.py`
- Existing promoted runtime contract enforced by `scripts/skill-hub-runtime`

## Success Criteria
- [ ] `skill-hub --cards "query"` in a real TTY shows governed rich cards, not only plain blocks.
- [ ] Pipe/non-TTY usage remains plain and agent-safe.
- [ ] No promoted runtime dependency on `src/cli/*` is reintroduced.
- [ ] Promotion and verify still pass with the complete runtime artifact set.
