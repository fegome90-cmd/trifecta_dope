# Design: Skill Hub Runtime UX Alignment

## Technical Approach

Realign the promoted runtime so every user-visible runtime frame needed after promotion lives under `scripts/`, while semantic authority stays in `scripts/skill_hub_cards_core.py`. The promoted surface becomes an explicit three-part contract: `scripts/skill-hub` as shell facade, `scripts/skill-hub-cards` plus a new adjacent promoted Python helper as runtime-owned UX layer, and `scripts/skill_hub_cards_core.py` as semantic authority.

This runtime does not have Engram, so the phase persists in OpenSpec/filesystem only; the design file is the source of truth for this phase.

## Architecture Decisions

| Decision | Choice | Alternatives considered | Rationale |
|---|---|---|---|
| Runtime UX home | Move intro/error framing into promoted `scripts/` code via a small adjacent helper module (for example `scripts/skill_hub_runtime_ux.py`) consumed by `scripts/skill-hub` and `scripts/skill-hub-cards` | Keep importing `src/cli/*`; duplicate prose inline in bash/Python | Promoted binaries cannot depend on `src/`; a governed adjacent helper keeps runtime UX shipped, testable, and explicit. |
| Semantic authority | Keep parse/normalize/classify/render-plan/exit-code semantics in `scripts/skill_hub_cards_core.py` | Let wrapper or helper infer renderability from prose/logs | The core already owns the authoritative decision path. Presentation must not become authority. |
| Role of `src/cli/*` | Preserve `src/cli/skill_cards.py` and `src/cli/error_cards.py` as repo-side renderers/reference implementations, not promoted runtime dependencies | Delete them; keep them authoritative for promoted runtime | They still serve repo CLI/internal callers, but promotion must not rely on unshipped code. |
| Promotion contract | Expand the governed promoted artifact/dependency set explicitly to include the runtime UX helper and verify it fail-closed | Hide helper as an undeclared side dependency | If a file is required at runtime, it must be in the receipt and dependency invariant. Hidden helpers recreate the exact authority bug we are fixing. |

## Data Flow

```text
user
  │
  ▼
scripts/skill-hub (public facade)
  ├─ help / arg validation
  ├─ stdout intro via scripts runtime UX helper
  ├─ delegates search/card path to skill-hub-cards
  └─ stderr error frames via scripts runtime UX helper
                 │
                 ▼
scripts/skill-hub-cards (runtime UX adapter)
  ├─ runs search/get through core entrypoints
  ├─ asks core for RenderPlan + exit code
  ├─ stdout: renderable cards only
  └─ stderr: non-renderable/runtime diagnostics only
                 │
                 ▼
scripts/skill_hub_cards_core.py (semantic authority)
  ├─ parse_search_output
  ├─ normalize_result / classify_result
  ├─ build_render_plan
  └─ EXIT_RENDERABLE / EXIT_ERROR / EXIT_NON_RENDERABLE / EXIT_EMPTY
```

Authority is the core-produced `RenderPlan` + exit code, plus promotion receipt/verify invariants. Intro text, banners, prompts, and error-card copy are mandatory evidence for UX, but never authority.

## File Changes

| File | Action | Description |
|---|---|---|
| `scripts/skill-hub` | Modify | Remove `src.cli.*` imports; keep shell orchestration, help flags, stream routing, and delegation to adjacent promoted helpers only. |
| `scripts/skill-hub-cards` | Modify | Stop owning ad hoc parsing/rendering logic; become runtime adapter that uses core authority and scripts-owned UX framing. |
| `scripts/skill_hub_cards_core.py` | Modify | Keep semantic authority unchanged except exposing the minimal stable hooks the runtime adapter needs. |
| `scripts/skill_hub_runtime_ux.py` | Create | Own intro rendering and governed stderr error-card formatting for the promoted runtime. |
| `src/cli/skill_cards.py` | Modify | Narrow to repo-side rendering/reference role; no promoted-runtime ownership. |
| `src/cli/error_cards.py` | Modify | Narrow to repo-side/reference error rendering; keep format parity where useful. |
| `tests/unit/test_skill_hub_runtime_promotion.py` | Modify | Update receipt/dependency invariants so the runtime helper is explicit and `src/` remains forbidden. |

## Interfaces / Contracts

- `scripts/skill_hub_cards_core.py` remains the only place that decides renderable vs non-renderable and exit codes.
- `scripts/skill_hub_runtime_ux.py` exposes presentation-only functions such as intro emission and stderr error-card formatting.
- `scripts/skill-hub-cards` may translate a `RenderPlan` into stdout/stderr output, but it MUST NOT reclassify results from text artifacts.

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Unit | Helper emits intro on stdout and error cards on stderr without semantic branching | Focused tests around runtime UX helper I/O contracts. |
| Unit | Core remains authority for classification and exit codes | Preserve/extend `skill_hub_cards_core` tests without making prose authoritative. |
| Integration | Wrapper + cards preserve stream split and fail-closed behavior | Subprocess tests for empty query, malformed payload, non-renderable result, and renderable success. |
| Promotion | Receipt/verifier include every real runtime dependency and reject `src/` coupling | Extend `tests/unit/test_skill_hub_runtime_promotion.py`. |

## Migration / Rollout

No data migration. Rollout is a contract realignment: the old design assumed promoted runtime could import `src/cli/*`; this design explicitly corrects that. The contradiction is resolved by promoting the real UX dependency set instead of letting repo-only files act as hidden authority.

## Open Questions

- None blocking. The only known limitation is persistence: hybrid was requested, but Engram is unavailable in this runtime, so persistence is filesystem/OpenSpec only.
