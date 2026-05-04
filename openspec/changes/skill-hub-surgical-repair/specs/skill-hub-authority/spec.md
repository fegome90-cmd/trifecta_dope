# Delta for Skill Hub Authority

## ADDED Requirements

### Requirement: Live skill-ref canonical matching

The alias canonical-match predicate in `scripts/skill-hub` MUST recognize exact `skill:{term}:` chunk ID refs in addition to legacy `repo:{term}.md:` refs. It MUST NOT match via substring or prefix — only exact ref family membership.

#### Scenario AUTH-001: live skill ref matched

- GIVEN an expansion with `skill:python-patterns:` in canonical hits
- WHEN alias rerank evaluates the ref
- THEN it SHALL recognize `skill:python-patterns:` as a canonical match
- AND produce the `Canonical alias match:` block

#### Scenario AUTH-002: legacy ref still matched

- GIVEN an expansion with `repo:python-patterns.md:` in canonical hits
- WHEN alias rerank evaluates the ref
- THEN it SHALL recognize `repo:python-patterns.md:` as a canonical match

#### Scenario AUTH-003: substring ref rejected

- GIVEN an expansion with `skill:python-patterns-extra:` in canonical hits
- WHEN alias rerank evaluates a query for `python-patterns`
- THEN it SHALL NOT match the extra ref as a canonical alias

### Requirement: Segment-scoped query lint defaults

The query linter `src/domain/query_linter.py` MUST accept an explicit segment or lint profile parameter. When the active segment is `skills-hub`, the linter MUST NOT inject entrypoint anchors (defined as: context-pack files listed in `configs/anchors.yaml` under `anchors.strong.files` — typically `agent.md`, `prime.md`) as vague-query defaults. Other segments MUST retain existing global anchor behavior.

Precedence chain (highest wins):
1. `lint_profile={"disable_entrypoint_anchors": True}` — always skips entrypoint anchors
2. `segment="skills-hub"` — skips entrypoint anchors for this segment
3. Default (no segment, no profile) — retains existing `agent.md`/`prime.md` injection

The segment source is `os.environ.get("TRIFECTA_SEGMENT")`, read in `src/infrastructure/cli.py` ctx search command, forwarded through `SearchUseCase` → `lint_query()` → `expand_query()`. No environment access in the domain layer.

#### Scenario AUTH-004: skills-hub segment excludes legacy anchors

- GIVEN a vague query (token_count <= 2) with `segment="skills-hub"`
- WHEN `expand_query()` processes the query
- THEN `added_strong` SHALL NOT contain `agent.md` or `prime.md`
- AND `reasons` SHALL NOT contain `"vague_default_boost"`

#### Scenario AUTH-005: default segment retains anchors

- GIVEN a vague query with no segment hint (segment=None) and no lint_profile
- WHEN `expand_query()` processes the query
- THEN it SHALL inject `agent.md` and/or `prime.md` as default anchors
- AND `reasons` SHALL contain `"vague_default_boost"`

#### Scenario AUTH-006: explicit profile overrides segment

- GIVEN a vague query and `lint_profile={"disable_entrypoint_anchors": True}`
- WHEN `expand_query()` processes the query (regardless of segment value)
- THEN it SHALL NOT inject entrypoint anchors
- AND `reasons` SHALL NOT contain `"vague_default_boost"`

### Requirement: Governed-only registration recovery

Broken registered skill entries MUST be repaired exclusively via `scripts/skill-hub-runtime promote` followed by `verify`. Manual edits to manifests, receipts, or promoted targets MUST be treated as evidence drift, not authority.

#### Scenario AUTH-007: promote repairs registration

- GIVEN a broken registered entry detected by `verify`
- WHEN `skill-hub-runtime promote` is executed from governed source
- THEN the entry SHALL be repaired with valid SHA and receipt
- AND `verify` SHALL report PASS

#### Scenario AUTH-008: manual edit rejected as authority

- GIVEN a receipt or promoted target that was hand-edited
- WHEN `skill-hub-runtime verify` runs
- THEN it SHALL detect the drift (SHA mismatch)
- AND SHALL report FAIL with the mismatched file path
