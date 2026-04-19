# Delta for skill-hub-authority

## ADDED Requirements

### Requirement: Governed first-impression composition

The system **MUST** render the `skill-hub` intro banner and sentence-query guidance through a repo-owned composer invoked by `scripts/skill-hub`. The composer **MUST** use governed card text and **MUST NOT** depend on hidden-authority legacy runtime helpers.

#### Scenario: banner and guidance render on start
- GIVEN a supported `skill-hub` invocation
- WHEN the entrypoint starts
- THEN the banner and query guidance SHALL render before classification output
- AND the rendered text SHALL come from governed repo code only

#### Scenario: legacy helper is absent
- GIVEN no `~/.local/bin` helper is present
- WHEN `skill-hub` starts
- THEN the intro path SHALL still render successfully
- AND no hidden-authority lookup SHALL be required

### Requirement: Stream-separated guidance and diagnostics

The system **MUST** keep user guidance and error cards on governed CLI streams. Informational intro content **SHOULD** go to stdout, diagnostics and fail-closed error cards **SHOULD** go to stderr, and the streams **MUST NOT** be mixed by ad hoc shell echoes.

#### Scenario: happy path output stays readable
- GIVEN a valid query
- WHEN intro and guidance render
- THEN stdout SHALL contain the banner and guidance
- AND stderr SHALL remain empty

#### Scenario: unsupported input is routed to error cards
- GIVEN empty, malformed, or unsupported input
- WHEN the request is handled
- THEN stderr SHALL contain the governed error card
- AND stdout SHALL not contain shell-echoed fallback prose

### Requirement: Exit codes are preserved under UX recovery

The system **MUST** preserve the existing exit code contract for success and failure states while changing only governed UX composition. A render or classification failure **MUST** fail closed and **MUST NOT** be normalized into success.

#### Scenario: success preserves zero
- GIVEN a valid query and successful render
- WHEN `skill-hub` exits
- THEN the exit code SHALL remain 0

#### Scenario: failure preserves non-zero behavior
- GIVEN malformed input or an internal render failure
- WHEN `skill-hub` exits
- THEN the existing non-zero exit code SHALL be preserved
- AND no hidden success path SHALL be introduced

### Requirement: Hidden-authority legacy runtime surfaces are prohibited

The system **MUST NOT** treat `/Users/felipe_gonzalez/.local/bin/skill_hub_info_card.py` or any other `~/.local/bin` legacy script as runtime authority. Such artifacts **MAY** be referenced only as non-authoritative comparison inputs in docs or tests.

#### Scenario: legacy surface is ignored
- GIVEN a legacy helper exists on disk
- WHEN runtime selection occurs
- THEN the helper SHALL be ignored as an authority surface
- AND the governed repo path SHALL remain authoritative

#### Scenario: comparison-only input is allowed
- GIVEN an engineer compares legacy output with governed output
- WHEN the comparison is performed in docs or tests
- THEN the legacy artifact MAY be used as reference only
- AND it SHALL NOT affect runtime decisions

## MODIFIED Requirements

### Requirement: Canonical-only downstream consumption

The system **MUST** read only the canonical manifest contract for semantic authority, and any runtime-visible UX surface that guides or frames `skill-hub` behavior **MUST** remain presentation-only. Aliases, guidance banners, and error cards **MUST NOT** become semantic authority surfaces.

#### Scenario: canonical consumer cutover
- GIVEN admitted canonical manifest state
- WHEN aliases, CLI skill metadata, banner guidance, or error cards are loaded
- THEN consumers SHALL read the canonical manifest surface only
- AND legacy `source_path`-style runtime reads SHALL be rejected

#### Scenario: derived aliases remain non-authoritative
- GIVEN aliases derived from the canonical manifest
- WHEN CLI expansion uses them
- THEN aliases SHALL be treated as convenience output only
- AND canonical manifest authority SHALL remain the sole semantic source

## REMOVED Requirements

### Requirement: Hidden-authority legacy runtime selection

(Reason: legacy home-bin runtime helpers are no longer acceptable authority surfaces for `skill-hub` UX or execution.)
