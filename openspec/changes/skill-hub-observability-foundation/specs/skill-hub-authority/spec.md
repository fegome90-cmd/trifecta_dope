# Delta for skill-hub-authority

## ADDED Requirements

### Requirement: Skill-hub runtime observability is local-first and canonical

The `skill-hub` runtime MUST persist structured local observability artifacts for each governed execution. Those local artifacts MUST be the canonical evidence source for runtime diagnostics and MUST remain available without network access or vendor credentials.

#### Scenario: local observability works offline
- GIVEN `skill-hub` runs without network access and without remote observability credentials
- WHEN the governed runtime completes a search or cards flow
- THEN it SHALL still persist local observability artifacts
- AND those artifacts SHALL be sufficient to explain the run outcome locally

#### Scenario: remote sink outage does not break canonical evidence
- GIVEN an optional remote sink is enabled but unavailable
- WHEN the governed runtime emits observability data
- THEN local artifact persistence SHALL still succeed
- AND the CLI semantic outcome SHALL remain governed by the local runtime pipeline, not by remote sink success

### Requirement: Skill-hub observability models pipeline stages explicitly

The governed runtime MUST emit structured observability events for the major `skill-hub` pipeline stages so the system can explain how raw hits became ranked results, renderable cards, and final output.

#### Scenario: hits-to-cards transformation is explainable
- GIVEN a query whose search hit count differs from its renderable card count
- WHEN the governed runtime builds the run summary
- THEN the summary SHALL include counts for hits, ranked results, promoted results, renderable cards, and dropped items
- AND it SHALL expose the reasons for dropped items in a structured form

#### Scenario: renderer route is explicit
- GIVEN the same semantic result set can render differently in TTY and non-TTY modes
- WHEN the governed runtime completes rendering
- THEN the local observability artifacts SHALL record the selected renderer route
- AND they SHALL distinguish between rich TTY and plain-safe output paths

### Requirement: Diagnostic output is derived from local summaries only

Any visible diagnostic output for `skill-hub` MUST be derived from the local run summary and MUST NOT compute or invent semantic truths independently.

#### Scenario: diagnostics remain presentation-only
- GIVEN diagnostic output is requested or enabled
- WHEN the runtime renders diagnostics
- THEN the diagnostic layer SHALL only display summary fields already derived from canonical local observability artifacts
- AND it SHALL NOT recalculate admission, classification, ranking, or exit-code semantics on its own

### Requirement: Optional remote sinks remain non-authoritative

Remote integrations for errors, logs, analytics, or export MUST remain adapters behind the local observability foundation. They MAY enrich visibility, but they MUST NOT become the authoritative runtime evidence source.

#### Scenario: Sentry sink enriches but does not replace local evidence
- GIVEN Sentry integration is enabled
- WHEN the runtime captures an exception or structured technical log
- THEN Sentry MAY receive correlated sink data
- AND the local observability artifacts SHALL still contain the canonical run evidence

#### Scenario: PostHog sink tracks usage without owning diagnostics truth
- GIVEN PostHog integration is enabled
- WHEN the runtime emits usage or product events
- THEN PostHog MAY receive those usage events
- AND the local run summary SHALL remain the source used for CLI diagnostics and technical explanation

## MODIFIED Requirements

### Requirement: Promoted runtime authority remains semantically separate from observability

The system MUST keep semantic authority in the governed `skill-hub` runtime pipeline while allowing observability to describe the pipeline. Observability MAY report semantic decisions and their reasons, but it MUST NOT change them.

#### Scenario: observability reports a degraded runtime without changing semantics
- GIVEN the governed runtime detects degraded config, receipt, or renderer state
- WHEN the runtime emits observability data and diagnostic output
- THEN the observability layer SHALL report the degraded condition faithfully
- AND the semantic pipeline SHALL still determine the official outcome and exit code

#### Scenario: diagnostic rendering does not become a hidden authority
- GIVEN the local summary contains counts, drop reasons, and renderer routing information
- WHEN diagnostic output is rendered in plain or rich form
- THEN the rendered diagnostics SHALL remain a presentation of the summary only
- AND any discrepancy between diagnostics and canonical local artifacts SHALL be treated as a contract violation
