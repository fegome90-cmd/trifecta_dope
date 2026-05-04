# mcp-silent-sync Specification

## Purpose
Ensure that the MCP server provides immediate value even in repositories that have not been manually indexed by Trifecta.

## Requirements

### Requirement: Silent Auto-Indexing
The MCP server SHALL automatically detect the absence of a Context Pack and perform an initial build before processing queries.

#### Scenario: Auto-Build on First Run
- GIVEN an MCP server started in a repository without a `_ctx/context_pack.json`
- WHEN the first RPC request (e.g., `initialize`) is received
- THEN the system SHALL trigger a silent `ctx_sync` operation in the background
- AND ensure the Context Pack is ready before fulfilling subsequent `ctx_search` calls.

#### Scenario: Existing Pack Validation
- GIVEN an MCP server started in a repository with an existing Context Pack
- WHEN the server starts
- THEN it SHALL skip the auto-indexing phase and use the existing pack.
