# Design: Skill Hub Surgical Repair

## Technical Approach

Surgical edits to 5 governed files. No new modules. The pipeline stays: search → normalize → classify → render. Each fix targets exactly one drift identified in exploration.

## Architecture Decisions

### Decision: Dual-family alias matching

**Choice**: Extend the Python inline in `scripts/skill-hub` to check both `repo:{term}.md:` and `skill:{term}:` ref prefixes. Matching is exact on the alias boundary: `f"skill:{term}:"` must match the ref prefix exactly — no partial prefix matching (e.g., `skill:python-pat:` does NOT match `skill:python-patterns:`). The `fullmatch` guard on `term` ensures the term itself is a clean slug.
**Alternatives**: Substring match on ref; regex pattern.
**Rationale**: Exact alias boundary match on two known families prevents false canonicals. The `fullmatch` guard on `term` already ensures the term itself is clean.

### Decision: Caller-provided segment hint and lint profile

**Choice**: Add optional `segment: str | None = None` and `lint_profile: dict | None = None` parameters to `expand_query()` and `lint_query()`. When `segment == "skills-hub"`, skip the `agent.md`/`prime.md` default injection block. When `lint_profile` contains `disable_entrypoint_anchors=True`, skip entrypoint injection regardless of segment. Profile overrides segment; segment overrides global defaults. All callers pass defaults — zero behavior change.
**Alternatives**: Environment variable check inside linter; separate linter function per segment; modify `configs/anchors.yaml`.
**Rationale**: Explicit parameters are testable and pure. No environment coupling in domain layer. `configs/anchors.yaml` stays untouched. Profile parameter covers the explicit-override scenario from spec.

### Decision: `skill_hub_cards_core.py` exports adapter; `runtime_ux.py` owns render model

**Choice**: Add `build_view_model(result: ClassifiedResult) -> RuntimeSkillCard` adapter in `cards_core.py` that bridges `ClassifiedResult` → the rendering model defined in `runtime_ux.py`. Import `RuntimeSkillCard` from `runtime_ux`. No separate `SkillCardViewModel` class — tests that import it get a type alias to `RuntimeSkillCard`.
**authority_state ownership**: `classify_result()` adds `authority_state` to the `ClassifiedResult` dataclass (new field, set at construction — frozen dataclass receives value via `dataclasses.replace()` or constructor). Healthy when all trusted fields (stable_id, visible_title, path, source, description) are present on the input `NormalizedResult`; degraded when some but not all are present. Results with no renderable data at all keep kind `UNSUPPORTED` (no view model produced). `build_view_model` reads `authority_state` from `ClassifiedResult`, does not derive it.
**RuntimeSkillCard canonical fields**: `id`, `name`, `path`, `source`, `description`, `authority_state` (healthy/degraded), `fidelity_level` ("full" | "partial" | "minimal"), `compact_flag` (bool — `fidelity_level != "full"`, i.e. True for both partial and minimal), `search_hints`, `triggers`, `relevance`. The adapter maps from `ClassifiedResult` fields. `fidelity_level` is derived by `build_view_model` from the number of trusted fields present: all present → "full", most present → "partial", only id/name → "minimal". `compact_flag = fidelity_level != "full"`.
**Alternatives**: Promote `SkillCardViewModel` from `src/application/`; duplicate render model in both files; let `build_view_model` own authority_state derivation.
**Rationale**: One render model (`RuntimeSkillCard`), one pipeline (`cards_core`), one UX facade (`runtime_ux`). Authority state belongs in classification — it's a classification concern, not a rendering concern.

### Decision: Renderer handoff via `_select_renderer`

**Choice**: `_select_renderer` in `cards_core.py` receives a `RenderPlan` containing view models (via `build_view_model`). Add `is_tty: bool` parameter to `_select_renderer`. It routes to `render_plain` (non-TTY or `style="plain"`) or `render_rich` (TTY + `style="rich"`). Both renderers consume `RuntimeSkillCard` instances from the plan. The handoff is: `ClassifiedResult` → `build_view_model()` → `RuntimeSkillCard` → stored in `RenderPlan.cards_vm` → `_select_renderer(plan, is_tty=sys.stdout.isatty())` → plain/rich output.
**SkillCard→RuntimeSkillCard field mapping**: The adapter maps: `SkillCard.title` → `RuntimeSkillCard.name`, `SkillCard.score` → `RuntimeSkillCard.relevance`. `render_plain` and `render_rich` in `cards_core.py` must be updated to access `card.name` (not `card.title`) and `card.relevance` (not `card.score`) when rendering from `RenderPlan.cards_vm`. The existing `RenderPlan.cards` (SkillCard list) remains for backward compat and JSON output.
**compact/TTY routing constraint**: `compact_flag` is always derived from the classified result's completeness. When TTY is available AND `style="rich"`, the rich renderer is used. When TTY is unavailable OR `style="plain"`, the plain renderer is used. `compact_flag` does NOT independently select a renderer — it's metadata on the view model consumed by whichever renderer is selected.
**Alternatives**: Separate renderer dispatcher; TTY detection in domain layer; keep render functions on SkillCard shape.
**Rationale**: `_select_renderer` already exists and routes by style flag. Updating render functions to use `RuntimeSkillCard` field names aligns the render pipeline with the single canonical view model. TTY detection stays in infrastructure, not domain.

### Decision: Pin banner to `render_intro()` from `runtime_ux.py`

**Choice**: `runtime_ux.py:render_intro()` is THE authority for intro/banner. Simple banner for non-TTY, hero for TTY. Already correct in current code — no logic change needed. `RuntimeSkillCard` gains `fidelity_level` and `compact_flag` fields but `render_intro()` is unaffected. Tests are characterization/pinning tests (GREEN from the start), not TDD RED→GREEN.
**Alternatives**: Move banner to cards_core; add config-driven banner.
**Rationale**: Code already implements the spec contract. Characterization tests pin existing behavior.

### Decision: Registration via promote/verify only

**Choice**: No code change to `scripts/skill-hub-runtime`. The fix is operational: run `promote` + `verify` from governed source. Tests assert that verify detects hand-edited receipts.
**Alternatives**: Add repair subcommand to skill-hub-runtime.
**Rationale**: The tooling already exists. Adding repair subcommands broadens attack surface for a one-time fix.

## Contract Details

### C1: Card Adapter API (`build_view_model`)

**Exported function**: `build_view_model(result: ClassifiedResult) -> RuntimeSkillCard | None` in `scripts/skill_hub_cards_core.py`

**Input**: `ClassifiedResult` dataclass with fields:
- `kind: str` — one of `RENDERABLE_SKILL`, `METADATA_ONLY`, `UNSUPPORTED`
- `normalized: NormalizedResult` — contains trusted fields
- `reason: str` — classification reason
- `authority_state: str` — `"healthy"` or `"degraded"`

**Output**:
- `RuntimeSkillCard` when `kind == RENDERABLE_SKILL`
- `None` when `kind != RENDERABLE_SKILL`

**Ownership**: `classify_result()` owns `authority_state`. `build_view_model()` reads it and derives `fidelity_level` + `compact_flag`.

**Dependency direction**: `cards_core.py` → `runtime_ux.py` (imports `RuntimeSkillCard`). Never reverse.

**Degraded behavior**: When `authority_state="degraded"`, `build_view_model()` counts trusted fields on `NormalizedResult`:
- 5/5 → `fidelity_level="full"`, `compact_flag=False`
- 3-4/5 → `fidelity_level="partial"`, `compact_flag=True`
- 1-2/5 (minimum `stable_id`) → `fidelity_level="minimal"`, `compact_flag=True`
- 0/5 → return `None` (not renderable)

**Trusted fields on NormalizedResult**: `stable_id`, `visible_title`, `path`, `source`, `description`

**Field mapping** (NormalizedResult → RuntimeSkillCard):
| Source | Target |
|--------|--------|
| `normalized.stable_id` | `id` |
| `normalized.visible_title` | `name` |
| `normalized.path` | `path` |
| `normalized.source` | `source` |
| `normalized.description` | `description` |
| `result.authority_state` | `authority_state` |
| derived from field count | `fidelity_level` |
| `fidelity_level != "full"` | `compact_flag` |

### C2: Query Linter Segment/Profile Precedence

**Source of segment**: `os.environ.get("TRIFECTA_SEGMENT")` read in `src/infrastructure/cli.py` (ctx search command). Passed as `segment: str | None` to `SearchUseCase` → `lint_query()` → `expand_query()`. Domain layer receives it as a pure parameter.

**Source of lint_profile**: Caller-provided `dict`. Currently only key: `disable_entrypoint_anchors: bool`. Future keys may be added without changing the function signature.

**Anchor exclusion flow** (inside `expand_query()`, lines ~102-112):
```
1. Profile override check:
   if lint_profile and lint_profile.get("disable_entrypoint_anchors"):
       SKIP entrypoint injection block entirely
       
2. Segment check:
   elif segment == "skills-hub":
       SKIP entrypoint injection block entirely
       
3. Default behavior (no segment, no profile override):
       EXECUTE existing agent.md/prime.md injection (unchanged)
```

**Regression guarantee**: When `segment=None` and `lint_profile=None`, `expand_query()` output is byte-identical to current behavior. Tests verify this by calling with no new params and comparing `added_strong`, `added_weak`, `reasons`.

**Propagation path**: `cli.py` → `search_get_usecases.py` → `lint_query()` → `expand_query()`. Each layer adds `**kwargs` passthrough or explicit `segment`/`lint_profile` params.

### C3: Renderer Handoff Boundary

**Router function**: `_select_renderer(plan: RenderPlan, *, use_json: bool, style: str, is_tty: bool = True)`

**Routing logic**:
```
if use_json:
    return json_renderer(plan.cards)       # backward compat, uses SkillCard[]
elif not is_tty or style == "plain":
    return render_plain(plan.cards_vm)      # uses RuntimeSkillCard[]
elif is_tty and style == "rich":
    return render_rich(plan.cards_vm)       # uses RuntimeSkillCard[]
```

**Plain renderer contract** (`render_plain(cards_vm: list[RuntimeSkillCard]) -> str`):
- Iterates `cards_vm`, accesses `card.name`, `card.relevance`, `card.path`
- Returns formatted plain-text string
- MUST NOT access `card.title` or `card.score`

**Rich renderer contract** (`render_rich(cards_vm: list[RuntimeSkillCard]) -> str`):
- Iterates `cards_vm`, accesses `card.name`, `card.relevance`, `card.path`, `card.description`
- Returns ANSI-formatted string
- MUST NOT access `card.title` or `card.score`

**`RenderPlan` extended fields**:
- `cards: list[SkillCard]` — existing, used for JSON output only
- `cards_vm: list[RuntimeSkillCard]` — new, used for plain/rich rendering

### C4: Intro/Banner TTY Decision

**Authority function**: `render_intro(rich: bool) -> str` in `scripts/skill_hub_runtime_ux.py`

**TTY decision point**: Caller determines TTY status via `sys.stdout.isatty()` in infrastructure (`cards_core.py` CLI entry or `scripts/skill-hub` bash wrapper). Passes `rich=True/False` to `render_intro()`. No `sys.stdout` access inside `render_intro()`.

**Plain output** (`rich=False`):
```
=== Skill Hub ===
<guidance sentence>
```

**Rich output** (`rich=True`):
```
<ASCII hero banner lines>
<guidance sentence>
```

**Pinning**: No code change needed. Characterization tests (GREEN) capture exact output of both variants.

### C5: Registration Recovery Operational Design

**Allowed commands** (in order):
1. `scripts/skill-hub-runtime verify` — identifies broken entries, reports SHA mismatches
2. `scripts/skill-hub-runtime promote` — repairs from governed source, writes valid receipt
3. `scripts/skill-hub-runtime verify` — confirms repair

**Evidence flow**: `promote` writes receipt with SHA of governed source content → `verify` recalculates SHA and compares → match = PASS, mismatch = FAIL.

**Prohibited write paths**: Manual edits to:
- `receipts/*.yaml` — only `promote` writes these
- `promoted/` targets — only `promote` writes these
- `configs/manifest.yaml` — only governed pipeline edits this

**Drift detection**: `verify` compares stored receipt SHA against current file SHA. Any mismatch → FAIL with file path. No automatic repair — `promote` must be run explicitly.

## Data Flow

```
skill-hub "query"
  ├── TRIFECTA_LINT=1 trifecta ctx search --explain --explain-format json
  │     └── lint_query(query, anchors, aliases, segment="skills-hub")  ← NEW param
  │           └── expand_query(segment="skills-hub"): skip agent.md/prime.md for skills-hub
  │                 (lint_query forwards segment/profile to expand_query)
  ├── alias_match(EXPLAIN_JSON)  ← MODIFIED: check skill:* + repo:*.md:
  └── run_search_capture() → output

skill-hub --cards "query"
  └── skill_hub_cards_core.cli()
        ├── parse_search_output() → RawSearchHit[]
        ├── normalize_result() → NormalizedResult
        ├── classify_result() → ClassifiedResult (+ authority_state)  ← EXTENDED
        ├── build_view_model() → RuntimeSkillCard  ← NEW adapter
        └── _select_renderer(plan, is_tty=...) → render via runtime_ux functions
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `scripts/skill-hub:176-188` | Modify | Add `skill:{term}:` prefix check alongside `repo:{term}.md:`; set `TRIFECTA_SEGMENT=skills-hub` env var |
| `src/infrastructure/cli.py` | Modify | Read `TRIFECTA_SEGMENT` env var in ctx search command, pass to search use case |
| `src/application/search_get_usecases.py` | Modify | Forward `segment` param to `lint_query()` |
| `src/domain/query_linter.py:expand_query,lint_query` | Modify | Add `segment` + `lint_profile` params; skip defaults when `skills-hub` or profile overrides; `lint_query` forwards both to `expand_query` |
| `scripts/skill_hub_cards_core.py` | Modify | Add `build_view_model()` adapter, extend `ClassifiedResult` with `authority_state` field, add `RenderPlan.cards_vm: list[RuntimeSkillCard]`, modify `classify_result()` to return `RENDERABLE_SKILL` with `authority_state="degraded"` when some (but not all) trusted fields are present (instead of `UNSUPPORTED`), update `render_plain`/`render_rich` to use `card.name`/`card.relevance` when consuming from `cards_vm` |
| `scripts/skill_hub_runtime_ux.py` | Modify | Add `fidelity_level: str = "full"` and `compact_flag: bool = False` fields to `RuntimeSkillCard` dataclass |
| `src/cli/skill_cards.py` | No change | Repo-side reference, not promoted |

## Interfaces / Contracts

```python
# src/domain/query_linter.py — extended signature
def expand_query(
    query: str, analysis: dict[str, Any],
    anchors_cfg: dict[str, Any],
    *, segment: str | None = None,
    lint_profile: dict | None = None,
) -> dict[str, Any]: ...

def lint_query(
    query: str, anchors_cfg: dict[str, Any],
    aliases_cfg: dict[str, Any],
    *, segment: str | None = None,
    lint_profile: dict | None = None,
) -> LinterPlan:
    """Forwards segment and lint_profile to expand_query."""
    ...

# Segment wiring: scripts/skill-hub sets TRIFECTA_SEGMENT=skills-hub env var.
# src/infrastructure/cli.py reads os.environ.get("TRIFECTA_SEGMENT") and passes to use case.
# src/application/search_get_usecases.py forwards segment to lint_query().

# scripts/skill_hub_cards_core.py — new adapter and extended types
from scripts.skill_hub_runtime_ux import RuntimeSkillCard

SkillCardViewModel = RuntimeSkillCard  # compatibility alias (optional, no current consumers)

@dataclass(frozen=True)
class ClassifiedResult:
    kind: str  # RENDERABLE_SKILL, METADATA_ONLY, UNSUPPORTED
    normalized: NormalizedResult
    reason: str
    authority_state: str = "healthy"  # NEW: "healthy" | "degraded"

def build_view_model(result: ClassifiedResult) -> RuntimeSkillCard | None:
    """Bridge classified result to the render model.
    Returns None when ClassifiedResult.kind != RENDERABLE_SKILL.
    authority_state comes from ClassifiedResult.
    fidelity_level derived from field completeness: full/partial/minimal.
    compact_flag = fidelity_level != "full"."""
    ...

@dataclass(frozen=True)
class RenderPlan:
    cards: list[SkillCard]         # backward compat, JSON output
    cards_vm: list[RuntimeSkillCard]  # NEW: for render_plain/render_rich
    # ... existing fields

def _select_renderer(plan: RenderPlan, *, use_json: bool, style: str, is_tty: bool = True):
    """Routes to render_plain (non-TTY or style=plain) or render_rich (TTY + style=rich).
    When consuming cards_vm, renderers use card.name/card.relevance (not title/score)."""
    ...
```

## Testing Strategy

| Layer | What to Test | Approach | Scenario Coverage |
|-------|-------------|----------|-------------------|
| Unit | `expand_query` with `segment="skills-hub"` excludes defaults | Direct call, assert `added_strong` doesn't contain `agent.md`/`prime.md` | AUTH-004 |
| Unit | `expand_query` with no segment retains defaults | Direct call, assert defaults injected | AUTH-005 |
| Unit | `expand_query` with profile overrides | Direct call, assert profile wins over segment | AUTH-006 |
| Unit | `expand_query` regression existing behavior | Call with no new params, compare output | AUTH-005 (baseline) |
| Unit | Alias match with `skill:*` refs | Inline Python snippet test | AUTH-001, AUTH-003 |
| Unit | Alias match with `repo:*` refs | Inline Python snippet test | AUTH-002 |
| Unit | `build_view_model` healthy | Feed `ClassifiedResult`, assert full `RuntimeSkillCard` | UX-001 |
| Unit | `build_view_model` degraded | Feed partial `ClassifiedResult`, assert degraded card | UX-002 |
| Unit | `build_view_model` non-renderable → None | Feed `METADATA_ONLY`, assert `None` | UX-003 |
| Unit | `_select_renderer` plain routing | Feed `RenderPlan` with `is_tty=False` | UX-004 |
| Unit | `_select_renderer` rich routing | Feed `RenderPlan` with `is_tty=True` | UX-005 |
| Unit | `render_intro(rich=False)` | Call and assert plain output | UX-006 |
| Unit | `render_intro(rich=True)` | Call and assert rich output | UX-007 |
| Integration | `skill-hub --cards` end-to-end | Run against `skills-hub` segment | UX-004, UX-005 |
| Unit | Verify detects manual edits | Mock receipt mismatch, assert FAIL | AUTH-008 |

## Migration / Rollout

No migration required. Changes are backward-compatible: `segment=None` preserves existing linter behavior; alias matching adds a new family without removing the legacy one.

## Resolved Questions

- authority_state ownership → `classify_result()` sets it on `ClassifiedResult` (new field, set at construction via `dataclasses.replace()`). `build_view_model` reads it. Not on `NormalizedResult`.
- scripts/ import path → implicit namespace package (Python 3). No `__init__.py` needed. Verified: `import scripts.skill_hub_runtime_ux` resolves.
- Phase 4 banner tests → characterization/pinning tests (GREEN), not TDD RED→GREEN. Code already correct.
- Segment wiring → Resolved: env var `TRIFECTA_SEGMENT=skills-hub` (set by bash script) → `src/infrastructure/cli.py` reads env → passes to `SearchUseCase` → forwards to `lint_query()`.

## Open Questions

None.
