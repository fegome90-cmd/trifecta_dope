# Delta for mcp-core-engine

## ADDED Requirements

### Requirement: Server Pre-flight Check
The MCP server MUST perform a pre-flight sanity check on the target repository before entering the main loop.

#### Scenario: Validate Repository Context
- GIVEN a repository path passed to the MCP server
- WHEN the server initializes
- THEN it SHALL verify the existence of the `skill.md` or trigger the `portable-bootstrap` flow
- AND report its readiness status via the `ctx_health` tool.
