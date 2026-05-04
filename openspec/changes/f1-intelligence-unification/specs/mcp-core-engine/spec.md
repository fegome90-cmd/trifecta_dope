# Delta for mcp-core-engine

## ADDED Requirements

### Requirement: Server Pre-flight Check
The MCP server MUST perform a pre-flight sanity check on the target repository before entering the main loop.

#### Scenario: Validate Repository Context
- GIVEN a repository path passed to the MCP server
- WHEN the server initializes
- THEN it SHALL verify the existence of the `skill.md` or trigger the `portable-bootstrap` flow
- AND report its readiness status via the `ctx_health` tool.

## MODIFIED Requirements

### Requirement: Direct UseCase Invocation
The MCP server SHALL import and execute Trifecta UseCases directly within its process memory, incorporating the Signal Fusion intelligence when available.
(Previously: The MCP server SHALL import and execute Trifecta UseCases directly within its process memory.)

#### Scenario: Direct Search Execution
- GIVEN a running MCP server in real mode
- WHEN the `ctx_search` tool is called with a query
- THEN the server SHALL invoke `src.application.intelligence_oracle.SearchOracleUseCase` (or its equivalent)
- AND return the structured JSON results without spawning a shell process.

#### Scenario: Fusion Intelligence Check
- GIVEN a search request
- WHEN the system processes the query
- THEN it SHALL check for LSP readiness
- AND if READY, it SHALL enrich search results with definition and symbol data from the LSP.
