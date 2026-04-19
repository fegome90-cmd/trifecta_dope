# Delta for skill-hub-authority

## ADDED Requirements

### Requirement: Default-path intro/render contract is governed

The system MUST render the default-path intro and sentence-query guidance through the governed runtime UX contract before any default-path search output. The default path MUST NOT skip or replace that intro renderer with an alternate local banner.

#### Scenario: default path renders the governed intro before search output
- GIVEN a valid query without `--cards`
- WHEN `skill-hub` runs on the default path
- THEN the governed intro/banner and sentence-query guidance SHALL render before search output
- AND the default-path search contract SHALL continue afterward

#### Scenario: default-path intro rendering stays governed after promotion
- GIVEN the promoted runtime is authoritative
- WHEN the same valid default-path query runs from the promoted runtime
- THEN the same governed intro/render contract SHALL be used
- AND the default path SHALL not invent a second banner or render surface

### Requirement: Cards flag admission is order-independent

The system MUST treat `--cards` as an admissible CLI mode selector regardless of argument position. The parsed route MUST depend on the final command contract, not on where the flag appears in the argv sequence.

#### Scenario: cards flag after query text
- GIVEN a valid query and `--cards` placed after the query text
- WHEN the command is parsed
- THEN the cards route SHALL activate
- AND the default search route SHALL NOT win by position alone

#### Scenario: cards flag before query text
- GIVEN a valid query and `--cards` placed before the query text
- WHEN the command is parsed
- THEN the cards route SHALL activate
- AND the selected route SHALL match the same semantic contract

### Requirement: Single-writer ownership is explicit per authority surface

The system MUST assign exactly one authorized writer to each authority surface covered by this change: default-path intro/render, cards presentation, promoted artifact publication, and doctor/verify evaluation. Any competing writer MUST be non-authoritative.

#### Scenario: one writer owns each surface
- GIVEN repo source and promoted runtime both exist
- WHEN authority is evaluated
- THEN each surface SHALL have exactly one authorized writer
- AND the non-authoritative side SHALL not claim ownership

### Requirement: Repo source and promoted runtime share one authority contract

The repository source and the promoted runtime MUST implement the same `skill-hub` authority contract for admission, routing, and presentation. A promoted artifact that diverges from the repo contract MUST be treated as stale and MUST NOT become authoritative.

#### Scenario: promoted runtime matches repo contract
- GIVEN a promoted runtime artifact set built from the repo source
- WHEN the command is invoked
- THEN the runtime SHALL behave according to the repo contract
- AND repo source and promoted behavior SHALL be equivalent for the same input

#### Scenario: promoted runtime drifts from repo source
- GIVEN a promoted runtime missing the repo-defined contract
- WHEN authority is evaluated
- THEN the runtime SHALL fail closed
- AND it SHALL NOT reinterpret the repo contract on its own

### Requirement: Promoted artifact set is complete or fail-closed

The system MUST promote the full runtime artifact set defined by the canonical artifact map in `skill-hub-runtime`. If any required runtime artifact is missing, malformed, or mismatched, promotion MUST fail closed and MUST NOT publish a partial authoritative runtime.

#### Scenario: complete promoted set
- GIVEN the canonical artifact map is complete and consistent
- WHEN promotion completes
- THEN the promoted set SHALL become authoritative as a single unit
- AND no required artifact SHALL be absent from the set

#### Scenario: required runtime artifact missing
- GIVEN a required runtime artifact is absent or unreadable
- WHEN promotion runs
- THEN promotion SHALL fail closed
- AND no partial runtime SHALL become visible

#### Scenario: promote and verify use the same artifact map
- GIVEN the canonical artifact map in the promotion surface
- WHEN `skill-hub-runtime promote` and `skill-hub-runtime verify` evaluate the set
- THEN both surfaces SHALL evaluate the same artifact membership and target names
- AND no artifact outside that map SHALL become authoritative

### Requirement: `skill-hub-runtime verify` is the operational doctor surface

The system MUST treat `skill-hub-runtime verify` as the operational doctor surface for the promoted artifact set. A passing verify result SHALL be the only operational proof that the promoted set is complete and current; failure MUST fail closed.

#### Scenario: verify passes on complete promoted set
- GIVEN the canonical promoted artifact set is present and matches the receipt
- WHEN `skill-hub-runtime verify` runs
- THEN the doctor surface SHALL report success
- AND the promoted set SHALL remain authoritative

#### Scenario: verify fails on drift or missing artifact
- GIVEN any promoted artifact is missing, unreadable, or hash-mismatched
- WHEN `skill-hub-runtime verify` runs
- THEN the doctor surface SHALL fail closed
- AND the promoted set SHALL NOT be treated as current authority

### Requirement: Default and cards paths share one semantic contract

The system MUST treat the default path and cards path as presentation routes under one semantic contract. The two paths MUST NOT define conflicting meanings for the same query, and route selection MUST NOT create a second authority surface.

#### Scenario: default path uses the shared contract
- GIVEN a valid query without `--cards`
- WHEN the command runs
- THEN the default path SHALL use the shared authority contract
- AND the cards contract SHALL remain inactive

#### Scenario: cards path uses the same shared contract
- GIVEN a valid query with `--cards`
- WHEN the command runs
- THEN the cards path SHALL use the same admitted query contract
- AND only the presentation route SHALL differ
