# Skill Hub Runtime UX Specification

## Purpose

Define the promoted-runtime contract for card view-model construction, renderer handoff, and intro/banner output behavior.

## Requirements

### Requirement: Single card view-model authority

The runtime card adapter `scripts/skill_hub_cards_core.py` SHALL be the sole authority for constructing renderable card state. It MUST produce a canonical view model consumed by all renderers, and MUST NOT delegate rendering decisions to competing models.

Adapter contract:
- **Owner**: `cards_core.py` exports `build_view_model()`
- **Input**: `ClassifiedResult` (from `classify_result()`)
- **Output**: `RuntimeSkillCard | None` (None when `kind != RENDERABLE_SKILL`)
- **Dependency direction**: `cards_core.py` imports `RuntimeSkillCard` from `runtime_ux.py` (cards_core → runtime_ux, never reverse)
- **Degraded behavior**: When `authority_state="degraded"`, `build_view_model()` still returns a `RuntimeSkillCard` with `fidelity_level="partial"` or `"minimal"` and `compact_flag=True`. Rendering continues without error.

Trusted fields on `NormalizedResult` for authority determination:
- `stable_id` — canonical skill identifier
- `visible_title` — display name
- `path` — filesystem path
- `source` — origin (promoted, indexed, etc.)
- `description` — skill description text

Fidelity levels:
- `"full"` — all 5 trusted fields present → `compact_flag=False`
- `"partial"` — 3-4 fields present → `compact_flag=True`
- `"minimal"` — 1-2 fields present (at minimum `stable_id`) → `compact_flag=True`

#### Scenario UX-001: card adapter produces view model

- GIVEN a `ClassifiedResult` with `kind=RENDERABLE_SKILL` and all 5 trusted fields present
- WHEN `build_view_model()` processes the result
- THEN it SHALL return a `RuntimeSkillCard` instance
- AND `authority_state` SHALL be `"healthy"`
- AND `fidelity_level` SHALL be `"full"`
- AND `compact_flag` SHALL be `False`
- AND the returned card SHALL have `id`, `name`, `path`, `source`, `description` fields populated

#### Scenario UX-002: degraded fallback

- GIVEN a `ClassifiedResult` with `kind=RENDERABLE_SKILL` and 3 of 5 trusted fields present
- WHEN `build_view_model()` processes the result
- THEN it SHALL return a `RuntimeSkillCard` instance
- AND `authority_state` SHALL be `"degraded"`
- AND `fidelity_level` SHALL be `"partial"`
- AND `compact_flag` SHALL be `True`
- AND rendering SHALL NOT raise an exception

#### Scenario UX-003: non-renderable produces None

- GIVEN a `ClassifiedResult` with `kind=METADATA_ONLY` or `kind=UNSUPPORTED`
- WHEN `build_view_model()` processes the result
- THEN it SHALL return `None`

### Requirement: Renderer handoff

The runtime `_select_renderer` function MUST hand renderable cards to the view-model renderer path. Plain-text and rich renderers SHALL consume the same view model type (`RuntimeSkillCard`).

Renderer contract:
- **Router**: `_select_renderer(plan: RenderPlan, *, use_json: bool, style: str, is_tty: bool = True)`
- **Plain renderer**: selected when `is_tty=False` or `style="plain"`
- **Rich renderer**: selected when `is_tty=True` AND `style="rich"`
- **Field access**: renderers MUST use `card.name` (not `card.title`) and `card.relevance` (not `card.score`)
- **Input**: `RenderPlan.cards_vm: list[RuntimeSkillCard]` (view models built by adapter)

#### Scenario UX-004: plain renderer handoff

- GIVEN a `RenderPlan` with `cards_vm` populated and `is_tty=False`
- WHEN `_select_renderer()` is invoked
- THEN it SHALL return the plain-text renderer
- AND the renderer SHALL consume `RenderPlan.cards_vm`
- AND the renderer SHALL access `card.name` and `card.relevance` from each `RuntimeSkillCard`

#### Scenario UX-005: rich renderer handoff

- GIVEN a `RenderPlan` with `cards_vm` populated and `is_tty=True` and `style="rich"`
- WHEN `_select_renderer()` is invoked
- THEN it SHALL return the rich renderer
- AND the renderer SHALL consume the same `RuntimeSkillCard` type
- AND the renderer SHALL access `card.name` and `card.relevance`

### Requirement: Intro/banner contract

The runtime intro output MUST be exactly two variants: simple `=== Skill Hub ===` for non-TTY/plain mode, optional ASCII hero for rich TTY mode. Both MUST be followed by sentence-query guidance text.

Decision point: `render_intro(rich: bool)` — the `rich` parameter is provided by the caller based on `sys.stdout.isatty()` detection in infrastructure. No TTY detection inside `render_intro` itself.

#### Scenario UX-006: plain intro output

- GIVEN `render_intro(rich=False)` is called
- WHEN intro is rendered
- THEN output SHALL start with `=== Skill Hub ===`
- AND SHALL contain a guidance sentence about query usage
- AND SHALL NOT contain ASCII hero art

#### Scenario UX-007: rich intro output

- GIVEN `render_intro(rich=True)` is called
- WHEN intro is rendered
- THEN output SHALL contain the ASCII hero banner lines
- AND SHALL contain a guidance sentence about query usage

#### Scenario UX-008: render_intro has only two variants

- GIVEN any runtime invocation of `render_intro`
- WHEN intro output is produced
- THEN it SHALL match exactly one of the two contracts above (rich=True or rich=False)
- AND no `render_intro`/`render_banner`/`print_intro` function SHALL exist outside `scripts/skill_hub_runtime_ux.py`
