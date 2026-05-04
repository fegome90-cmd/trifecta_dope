# Delta for mcp-core-engine

## MODIFIED Requirements

### Requirement: Server Pre-flight Check
The MCP server MUST perform a pre-flight sanity check on the target repository before entering the main loop, including support for the SYNCING state.
(Previously: Synchronous check that could block startup)

#### Scenario: Report SYNCING state in Health
- GIVEN a repository where a silent sync is currently in progress
- WHEN the `ctx_health` tool is called
- THEN the system SHALL return `state: SYNCING`
- AND include information about the active lock.

#### Scenario: Fail-Closed on Timeout
- GIVEN a server that failed to reach READY state due to a timeout
- WHEN any context-dependent tool (e.g., `ctx_search`) is called
- THEN the system SHALL return a structured error with the `FAILED` state description.
