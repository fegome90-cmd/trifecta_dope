# Design: Skill-hub Rich Runtime Renderer

## Technical Approach

Extend the governed runtime presentation layer so rich card rendering lives under promoted `scripts/` code, while semantic ownership remains in `scripts/skill_hub_cards_core.py`.

The runtime will keep one semantic card pipeline and choose presentation mode at the last moment:
- **TTY** → governed rich renderer
- **non-TTY / pipe / agent** → governed plain renderer

This preserves the architecture we already repaired:
- **semantic authority** stays in `skill_hub_cards_core.py`
- **presentation authority** stays in runtime-owned `scripts/` presentation code
- **promotion/verification authority** stays in `skill-hub-runtime`
- **repo-side `src/cli/*` remains reference-only**

## Architecture Decisions

| Decision | Choice | Alternatives considered | Rationale |
|---|---|---|---|
| Rich renderer ownership | Rich card rendering lives in governed `scripts/` runtime code | Reuse `src/cli/skill_cards.py` directly | Reusing `src/cli/*` would reintroduce repo/runtime coupling and break promoted-runtime self-containment. |
| Semantic vs presentation split | `skill_hub_cards_core.py` keeps parse/classify/exit decisions; renderer only formats `RuntimeSkillCard` view models | Let rich renderer infer or adjust card meaning | Presentation must not own semantics. One semantic pipeline prevents split-brain. |
| Style routing | Runtime chooses rich vs plain by output context (TTY or not) | Force one style globally; add user-facing style flags first | Context-based routing preserves human UX while keeping agent/pipe safety. |
| Implementation shape | Expand `scripts/skill_hub_runtime_ux.py` or add adjacent runtime-owned renderer helper under `scripts/` | Keep all logic inline in shell wrapper | Python-side renderer keeps formatting testable and promotes as one governed unit. |
| Promotion contract | Any runtime-owned renderer code required by rich mode must be in the canonical artifact map | Treat rich renderer as optional/local convenience | If TTY rich is part of the contract, promotion must fail closed when those artifacts are missing. |

## Data Flow

```text
search payload
  -> scripts/skill_hub_cards_core.py
     -> parse / normalize / classify
     -> build runtime card view models
     -> inspect stdout context
     -> rich mode if TTY, plain mode otherwise
     -> delegate rendering to governed runtime UX renderer
runtime promotion
  -> scripts/skill-hub-runtime promote
  -> copy wrapper + cards adapter + runtime UX/renderer artifacts + core
runtime verification
  -> scripts/skill-hub-runtime verify
  -> ensure full renderer-capable artifact set is present and byte-matched
```

## File Changes

| File | Action | Description |
|---|---|---|
| `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill_hub_runtime_ux.py` | Modify | Add governed rich card renderer plus shared TTY/plain presentation helpers. |
| `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill_hub_cards_core.py` | Modify | Select runtime presentation mode while preserving semantic and exit-code authority. |
| `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill-hub-cards` | Maybe Modify | Keep adapter aligned if renderer entry contract changes. |
| `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/scripts/skill-hub-runtime` | Maybe Modify | Maintain complete promotion/verify contract for any expanded runtime UX artifact surface. |
| `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/tests/unit/test_skill_hub_cards_governed.py` | Modify | Verify governed rich rendering behavior in runtime paths. |
| `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/tests/unit/test_skill_hub_render_parity.py` | Modify | Prove rich/plain presentation parity over the same semantic card model. |
| `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/tests/unit/test_skill_hub_runtime_promotion.py` | Modify | Ensure promoted artifact set remains complete for rich runtime rendering. |
| `/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/tests/unit/test_skill_hub_runtime_ux.py` | Modify | Validate rich/plain intro and card rendering helpers under TTY/non-TTY conditions. |

## Interfaces / Contracts

- `skill_hub_cards_core.py` remains the only owner of:
  - search output parsing
  - normalization
  - classification
  - exit-code selection
- `skill_hub_runtime_ux.py` (or a governed sibling under `scripts/`) owns:
  - intro/banner rendering
  - error-card rendering
  - rich card formatting
  - plain card formatting
- Rich rendering must consume the same `RuntimeSkillCard` model used by plain rendering.
- The runtime must forbid direct imports from `src/cli/skill_cards.py` in promoted execution paths.

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Unit | rich/plain renderer behavior, TTY routing, degraded-card visibility | pytest on runtime UX and core routing helpers |
| Parity | same card identities/outcomes survive in rich and plain | focused parity tests on runtime view models |
| Promotion | promoted runtime includes all renderer artifacts and fails closed on missing pieces | `skill-hub-runtime` promotion/verify tests |
| Real usage | `skill-hub --cards "query"` in TTY shows rich cards; non-TTY remains plain | focused smoke checks |

## Migration / Rollout

No semantic migration. Rollout sequence:
1. implement governed rich runtime renderer,
2. verify TTY/non-TTY split with focused tests,
3. promote full runtime artifact set,
4. smoke-test real `skill-hub --cards` usage in TTY.

## Open Questions

- [ ] Whether the rich renderer should use `rich` panels directly inside `scripts/skill_hub_runtime_ux.py` or via a small adjacent governed helper module for cleaner separation inside `scripts/`.
