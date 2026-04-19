# Delta for skill-hub-authority

## ADDED Requirements

### Requirement: TTY card rendering is governed and rich

The promoted runtime MUST render skill cards through a governed rich presentation surface when `skill-hub` or `skill-hub --cards` is used in an interactive TTY. The rich renderer MUST remain presentation-only and MUST NOT change admission, classification, ranking, or exit-code semantics.

#### Scenario: rich renderer activates for renderable cards in TTY
- GIVEN a renderable skill result set in an interactive TTY
- WHEN the governed runtime renders skill cards
- THEN the output SHALL use the governed rich card renderer
- AND the semantic outcome and exit code SHALL match the underlying render plan

#### Scenario: rich renderer does not take semantic ownership
- GIVEN the governed runtime rich renderer is active
- WHEN the same search payload is classified
- THEN admission, normalization, classification, and exit code SHALL still be decided by `skill_hub_cards_core.py`
- AND the rich renderer SHALL only consume the presentation model

### Requirement: Non-TTY card rendering remains plain and agent-safe

The governed runtime MUST preserve plain text rendering for non-TTY, redirected, piped, or agent-consumed execution paths.

#### Scenario: non-TTY path stays plain
- GIVEN a renderable skill result set and stdout is not a TTY
- WHEN the governed runtime renders skill cards
- THEN the output SHALL remain plain text
- AND it SHALL not emit rich panel framing or terminal-only visual decoration

### Requirement: Runtime rich renderer is self-contained

The promoted runtime MUST NOT depend on repo-side `src/cli/*` reference renderers to provide rich card output. Any rich runtime renderer used in production MUST live in the governed promoted artifact set.

#### Scenario: runtime rich renderer avoids repo-side imports
- GIVEN the governed runtime artifact set is promoted
- WHEN the runtime renders cards in rich mode
- THEN no promoted runtime module SHALL require `src/cli/skill_cards.py` or other repo-side reference renderers
- AND the runtime SHALL remain complete using only promoted governed artifacts

### Requirement: Rich and plain routes share one card semantics contract

Rich and plain skill-card rendering MUST consume the same semantic card model. Presentation mode MAY affect formatting only; it MUST NOT change which cards are shown, their meaning, or the associated exit code.

#### Scenario: rich and plain modes preserve card identity
- GIVEN the same renderable search payload
- WHEN the runtime renders once in TTY rich mode and once in non-TTY plain mode
- THEN both outputs SHALL represent the same underlying card identities and outcome kind
- AND only formatting/presentation SHALL differ

#### Scenario: degraded cards remain semantically consistent across modes
- GIVEN a degraded renderable card
- WHEN the runtime renders in rich and plain modes
- THEN both modes SHALL surface the degraded state
- AND neither mode SHALL silently hide or reinterpret that authority state

## MODIFIED Requirements

### Requirement: Promoted artifact set is complete or fail-closed

The system MUST promote the full runtime artifact set defined by the canonical artifact map in `skill-hub-runtime`, including any governed rich runtime renderer surface required for TTY presentation. If any required runtime artifact is missing, malformed, or mismatched, promotion MUST fail closed and MUST NOT publish a partial authoritative runtime.

#### Scenario: rich renderer artifacts are included in the promoted set
- GIVEN the governed runtime supports rich TTY rendering
- WHEN promotion completes
- THEN every runtime-owned artifact required for rich rendering SHALL be present in the promoted artifact set
- AND verify SHALL treat missing rich renderer artifacts as a fail-closed contract violation

#### Scenario: malformed or mismatched rich renderer artifacts fail closed
- GIVEN a governed rich renderer artifact is malformed, byte-mismatched, or otherwise inconsistent with the canonical promoted artifact set
- WHEN `skill-hub-runtime verify` evaluates the promoted runtime
- THEN verify SHALL fail closed
- AND the promoted runtime SHALL NOT remain authoritative until the artifact set is corrected
