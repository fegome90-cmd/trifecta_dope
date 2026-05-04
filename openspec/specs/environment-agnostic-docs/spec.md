# environment-agnostic-docs Specification

## Purpose
Maintain a clean and shareable repository state by removing machine-specific path details from documentation and persistent log artifacts.

## Requirements

### Requirement: Absolute Path Redaction in Artifacts
All documentation and log artifacts MUST use generic placeholders instead of absolute local paths.

#### Scenario: Placeholder replacement in logs
- GIVEN a telemetry or reconciliation log file
- WHEN a path containing the user's home directory is recorded
- THEN the system SHALL replace the machine-specific prefix with `<REPO_ROOT>`.

### Requirement: Documentation Portability
SDD artifacts and architecture reports MUST be portable across machines.

#### Scenario: Verify Proposal paths
- GIVEN an SDD proposal document
- WHEN referencing a file location in the repository
- THEN the path SHALL be relative to the repository root
- AND any absolute path references MUST use the `<REPO_ROOT>` placeholder.
