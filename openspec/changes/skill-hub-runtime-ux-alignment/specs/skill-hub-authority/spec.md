# Delta for skill-hub-authority

## ADDED Requirements

### Requirement: Promoted runtime UX is self-contained

The promoted `skill-hub` runtime MUST resolve intro and error framing only from promoted `scripts/` artifacts. It MUST NOT depend on `src/` imports, unshipped helpers, or hidden-authority fallback prose.

#### Scenario: promoted entrypoint runs without src
- GIVEN a promoted runtime environment with no `src/` on path
- WHEN `scripts/skill-hub` or `scripts/skill-hub-cards` runs
- THEN intro/error framing SHALL render from promoted code
- AND no `src/` module import SHALL be required

#### Scenario: promoted framing artifacts are missing
- GIVEN a required promoted framing artifact is absent or malformed
- WHEN the runtime starts
- THEN the command SHALL fail closed
- AND it SHALL NOT fall back to `src/` or legacy prose

### Requirement: Intro and error framing remain presentation-only

The promoted runtime MUST provide intro framing and error cards under `scripts/` without turning prompts, helper text, or presentation templates into semantic authority. Canonical manifest and governed classification remain the sole semantic authority.

#### Scenario: prose changes do not change authority
- GIVEN valid canonical manifest data
- WHEN intro, prompt, or error copy changes
- THEN admission and classification behavior SHALL remain unchanged
- AND helper text SHALL not alter authority decisions

#### Scenario: presentation text is not authoritative
- GIVEN a banner, prompt, or error card is rendered
- WHEN a consumer reads the runtime output
- THEN the output SHALL be treated as presentation only
- AND no semantic decision SHALL be derived from that text

### Requirement: Output streams and exit codes remain stable

The promoted runtime MUST keep informational intro content on stdout, diagnostics on stderr, and existing success/failure exit codes unchanged.

#### Scenario: happy path preserves streams
- GIVEN a valid query and successful promotion
- WHEN the runtime renders intro and guidance
- THEN stdout SHALL contain the intro/banner text
- AND stderr SHALL remain empty

#### Scenario: failure preserves diagnostics and exit status
- GIVEN malformed input or a runtime rendering failure
- WHEN the command exits
- THEN stderr SHALL contain the governed error card
- AND the existing non-zero exit code SHALL be preserved

## MODIFIED Requirements

### Requirement: Canonical-only downstream consumption

The system **MUST** read only the canonical manifest contract for semantic authority, and any runtime-visible UX surface that guides or frames `skill-hub` behavior **MUST** remain presentation-only. Aliases, promoted intro banners, promoted error cards, and helper prompts **MUST NOT** become semantic authority surfaces.
(Previously: runtime-visible UX framing was not explicitly pinned to the promoted artifact set.)

#### Scenario: canonical consumer cutover
- GIVEN admitted canonical manifest state
- WHEN aliases, CLI skill metadata, banners, prompts, or error cards are loaded
- THEN consumers SHALL read the canonical manifest surface only
- AND legacy `source_path`-style runtime reads SHALL be rejected

#### Scenario: derived aliases remain non-authoritative
- GIVEN aliases derived from the canonical manifest
- WHEN CLI expansion uses them
- THEN aliases SHALL be treated as convenience output only
- AND canonical manifest authority SHALL remain the sole semantic source
