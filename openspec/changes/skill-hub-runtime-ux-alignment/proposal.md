# Proposal: Skill Hub Runtime UX Alignment

## Intent
Align the promoted `skill-hub` runtime with the gate finding: promoted binaries cannot depend on `src/`, so intro/error framing must live in promoted `scripts/` code. This closes the fallback-to-inline-prose gap and keeps governed UX available after promotion.

## Scope

### In Scope
- Move runtime-owned intro + error framing into promoted `scripts/` code.
- Make `scripts/skill-hub` and `scripts/skill-hub-cards` use only promoted helpers.
- Update the authority contract so promoted UX is owned by the runtime surface.

### Out of Scope
- Broad CLI redesign.
- Reintroducing `src.cli.*` as runtime authority.
- Changing canonical admission/promotion semantics beyond the UX split.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `skill-hub-authority`: promoted runtime UX becomes part of the governed contract; intro/error framing must be present in the promoted artifact set and may not rely on unshipped `src/` modules.

## Approach
Keep semantic authority in the governed core, but move the runtime UX contract into promoted `scripts/` code. Treat `src/cli/skill_cards.py` and `src/cli/error_cards.py` as canonical references only unless promotion is expanded later. This corrects the prior recovery assumption that `src/` was available after promotion — it is not.

## Ownership / Single Writer
Per `openspec/config.yaml`, each authority surface must have exactly one writer:

| Authority surface | Single writer | Notes |
|---|---|---|
| Governing capability contract | `openspec/specs/skill-hub-authority/spec.md` | Canonical behavior and invariants. |
| Runtime UX framing in promoted artifacts | `scripts/skill_hub_runtime_ux.py` | Single promoted writer for intro/error framing after promotion. |
| Core parse/classify/render-plan logic | `scripts/skill_hub_cards_core.py` | Owns semantic decisions only. |
| Reference renderers under `src/cli/` | `src/cli/skill_cards.py` and `src/cli/error_cards.py` | Reference-only; not runtime authority. |
| Test contract for promoted boundary | `tests/unit/test_skill_hub_runtime_promotion.py` | Guards the promoted surface contract. |

## Affected Areas
| Area | Impact | Description |
|---|---|---|
| `openspec/specs/skill-hub-authority/spec.md` | Modified | Clarify runtime-visible UX authority. |
| `scripts/skill_hub_runtime_ux.py` | New | Promoted-only intro/error helper for runtime UX framing. |
| `scripts/skill-hub` | Modified | Use promoted intro/error helpers only. |
| `scripts/skill-hub-cards` | Modified | Emit governed UX without `src/` imports. |
| `scripts/skill_hub_cards_core.py` | Modified | Keep classify/render-plan authority unchanged. |
| `src/cli/skill_cards.py` | Reference-only | Retained as canonical reference renderer unless promotion expands. |
| `src/cli/error_cards.py` | Reference-only | Retained as canonical reference renderer unless promotion expands. |
| `tests/unit/test_skill_hub_runtime_promotion.py` | Modified | Pin promoted runtime independence from `src/`. |

## Risks
| Risk | Likelihood | Mitigation |
|---|---|---|
| Hidden authority via `src/` imports | High | Keep promoted paths self-contained; test promotion-time import failure as non-authoritative. |
| UX regression while moving framing | Med | Preserve stdout/stderr split and exit codes. |
| Spec drift with the prior recovery proposal | Med | State the corrected contract explicitly in spec and tests. |

## Rollback Plan
Revert the UX helper move and restore the last governed promoted flow, but do not restore any `src/` dependency in the promoted runtime. If needed, fall back to the existing promoted text path while keeping the authority boundary fail-closed.

## Dependencies
- Existing `skill-hub-authority` spec.
- Filesystem/OpenSpec persistence only; Engram is unavailable in this runtime.

## Success Criteria
- [ ] Promoted `skill-hub` no longer depends on `src/` for intro/error framing.
- [ ] Governed UX is available from promoted `scripts/` code.
- [ ] The authority spec states the runtime-visible UX contract unambiguously.
