# Delta for mcp-search-get

## MODIFIED Requirements

### Requirement: Context Retrieval Mode Support
The `ctx_get` tool MUST support multiple retrieval modes (raw, excerpt, skeleton) and enforce token budgets.
(Previously: Fixed retrieval with manual regex sanitization)

#### Scenario: Skeleton Retrieval for Design
- GIVEN a list of chunk IDs
- WHEN the agent calls `ctx_get` with mode="skeleton"
- THEN the system SHALL invoke `GetChunkUseCase` with mode="skeleton"
- AND return only signatures and docstrings to save token budget.

#### Scenario: PII-Safe Retrieval
- GIVEN a chunk containing sensitive information
- WHEN `ctx_get` is called
- THEN the system SHALL use Trifecta's core sanitization logic
- AND ensure no secrets are exposed in the MCP response.
