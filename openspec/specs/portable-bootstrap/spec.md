# portable-bootstrap Specification

## Purpose
Enable zero-config initialization of context packs via the MCP interface, allowing any repository to be indexed in a single pass.

## Requirements

### Requirement: One-Pass Context Initialization
The system SHALL provide a `ctx_init` tool to scaffold and index a repository if context is missing.

#### Scenario: Initialization of New Repo
- GIVEN an MCP server running on a directory without a `_ctx/` folder
- WHEN the agent calls `ctx_init`
- THEN the system SHALL run the equivalent of `trifecta create` and `trifecta ctx build`
- AND respond with a success status and the number of indexed chunks.
