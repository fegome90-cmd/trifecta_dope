# mcp-core-engine Specification

## Purpose
Define the core integration between the MCP protocol and Trifecta's internal application layer (UseCases), ensuring zero-latency communication and zero subprocess overhead.

## Requirements

### Requirement: Direct UseCase Invocation
The MCP server SHALL import and execute Trifecta UseCases directly within its process memory.

#### Scenario: Direct Search Execution
- GIVEN a running MCP server in real mode
- WHEN the `ctx_search` tool is called with a query
- THEN the server SHALL invoke `src.application.search_get_usecases.SearchUseCase` directly
- AND return the structured JSON results without spawning a shell process.

### Requirement: Skill-Hub Performance Layer
The system MUST leverage Skill-Hub metadata (when available) to pre-filter and prioritize search results.

#### Scenario: Metadata-Aware Search
- GIVEN a repository with a valid `skills_manifest.json`
- WHEN a query matches a keyword in the manifest
- THEN the system SHALL prioritize chunks from that specific skill
- AND return results with a "source: skill-hub" metadata flag.
# Delta for mcp-core-engine

## ADDED Requirements

### Requirement: Server Pre-flight Check
The MCP server MUST perform a pre-flight sanity check on the target repository before entering the main loop.

#### Scenario: Validate Repository Context
- GIVEN a repository path passed to the MCP server
- WHEN the server initializes
- THEN it SHALL verify the existence of the `skill.md` or trigger the `portable-bootstrap` flow
- AND report its readiness status via the `ctx_health` tool.
