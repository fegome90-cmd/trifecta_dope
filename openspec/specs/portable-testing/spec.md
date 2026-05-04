# portable-testing Specification

## Purpose
Ensure that all tests in the Trifecta repository can be executed in any environment (local, CI, clean machine) without failing due to machine-specific absolute path hardcoding.

## Requirements

### Requirement: Dynamic Root Resolution in Tests
All tests MUST resolve the repository root dynamically instead of using hardcoded absolute paths.

#### Scenario: Verify acceptance tests run anywhere
- GIVEN a Trifecta repository cloned to a non-standard location (e.g., `/tmp/test-repo`)
- WHEN `pytest tests/acceptance` is executed
- THEN the tests SHALL correctly identify the repository root relative to the test file
- AND no tests SHALL be skipped due to "Requires local development environment" unless a real dependency is missing.

### Requirement: Environment-Agnostic Skip Logic
Test skipping logic MUST NOT depend on the existence of a specific user's home directory path.

#### Scenario: Dynamic path validation in SkipIf
- GIVEN a test module with `pytest.mark.skipif`
- WHEN the condition checks for repository existence
- THEN it SHALL use a dynamically resolved path (e.g., via a fixture or utility) instead of a hardcoded string like `<REPO_ROOT>/...`.
