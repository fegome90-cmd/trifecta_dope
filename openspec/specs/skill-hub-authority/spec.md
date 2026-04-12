# Skill Hub Authority Specification

## Purpose

Define the single-authority runtime contract for `skill_hub`: canonical manifest admission, atomic promotion of the promoted artifact set, canonical pack-only runtime, and canonical-only downstream consumers.

## Requirements

### Requirement: Single authority per surface

The system **MUST** assign exactly one authorized writer to each `skill_hub` surface: staging input, canonical manifest, canonical pack, promotion transaction/promoted set, admission receipt, runtime load surface, and aliases/CLI consumption surface.

#### Scenario: one writer per surface
- GIVEN a segment with `indexing_policy=skill_hub`
- WHEN authority is evaluated
- THEN each surface SHALL have exactly one authorized writer
- AND any competing writer SHALL be non-authoritative

### Requirement: Canonical admission boundary

The system **MUST** treat external or legacy-compatible manifest input as staging only and **MUST** normalize it before any runtime-visible artifact exists.

#### Scenario: staging input normalized before authority
- GIVEN external manifest-like inventory
- WHEN `skill_hub` admission runs
- THEN the input SHALL be consumed only by the normalization boundary
- AND only the canonical manifest SHALL become authoritative

#### Scenario: invalid staging input
- GIVEN malformed, stale, or unresolved staging input
- WHEN admission runs
- THEN admission SHALL fail closed
- AND no promoted artifact set SHALL be published

### Requirement: Atomic promotion of the promoted artifact set

The system **MUST** publish the canonical manifest, canonical pack, and promotion receipt as one promoted artifact set and **MUST NOT** expose partial promotion to runtime.

#### Scenario: successful promotion
- GIVEN canonical manifest and matching canonical pack candidate
- WHEN promotion succeeds
- THEN manifest, pack, and receipt SHALL become visible as one set
- AND runtime SHALL read that promoted set only

#### Scenario: partial promotion failure
- GIVEN a failure before receipt publication
- WHEN promotion aborts
- THEN no new artifact SHALL become runtime-visible
- AND the last promoted valid set SHALL remain active

### Requirement: Canonical skill_hub pack only

The system **MUST** admit only `skill_hub`-shaped packs and **MUST NOT** accept generic-shaped packs for `skill_hub`.

#### Scenario: canonical pack admitted
- GIVEN a canonical manifest and matching skill files
- WHEN the pack is evaluated for promotion
- THEN all chunk ids SHALL be `skill:*`
- AND the pack SHALL exclude `repo:`, `prime:`, `agent:`, and `session:` families

#### Scenario: non-canonical pack rejected
- GIVEN a `skill_hub` pack candidate containing metadata or generic chunk families
- WHEN admission evaluates the pack
- THEN the pack SHALL be rejected
- AND runtime SHALL not treat it as valid

### Requirement: No generic fallback for skill_hub

The system **MUST NOT** downgrade a declared `skill_hub` segment to `generic` behavior.

#### Scenario: invalid authority state
- GIVEN a segment declared as `skill_hub`
- WHEN manifest, pack, policy consistency, or provenance is invalid
- THEN the system SHALL fail closed
- AND it SHALL NOT switch to generic indexing or generic runtime semantics

### Requirement: Canonical-only downstream consumption

Aliases and CLI consumers **MUST** read only the canonical manifest contract, and derived aliases **MUST NOT** become a semantic authority surface.

#### Scenario: canonical consumer cutover
- GIVEN admitted canonical manifest state
- WHEN aliases or CLI skill metadata are loaded
- THEN consumers SHALL read the canonical manifest surface only
- AND legacy `source_path`-style runtime reads SHALL be rejected

#### Scenario: derived aliases remain non-authoritative
- GIVEN aliases derived from the canonical manifest
- WHEN CLI expansion uses them
- THEN aliases SHALL be treated as convenience output only
- AND canonical manifest authority SHALL remain the sole semantic source
