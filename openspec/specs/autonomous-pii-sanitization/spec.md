# autonomous-pii-sanitization Specification

## Purpose
Enforce a centralized "Zero Trust Path" policy across all Trifecta signals.

## Requirements

### Requirement: Centralized Redaction Policy
The system MUST use a single, domain-level service to redact absolute paths and secrets.

#### Scenario: Telemetry Redaction
- GIVEN a telemetry event containing `/Users/felipe/...`
- WHEN the event is persisted
- THEN the system SHALL replace the absolute path with `<ABS_PATH_REDACTED>`.

### Requirement: Cross-Signal Sanitization
All tool responses (MCP, CLI, Oracle) SHALL be sanitized using the same rules.

#### Scenario: Oracle response safety
- GIVEN a search hit for a local file
- WHEN returned via the Oracle
- THEN the system SHALL ensure no absolute local paths are leaked in the metadata or preview.
