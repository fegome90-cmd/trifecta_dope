# mcp-backpressure-mgmt Specification

## Purpose
Enable the MCP server to handle long-running operations (like initial indexing) gracefully without blocking agents indefinitely.

## Requirements

### Requirement: Asynchronous Context Readiness
The server SHALL execute `ensure_context_ready` in a way that allows monitoring progress and enforcing timeouts.

#### Scenario: Build Timeout with Error
- GIVEN an MCP server in a large repository without a Context Pack
- WHEN a tool call triggers a silent sync
- AND the sync operation exceeds the configured `BUILD_TIMEOUT`
- THEN the server MUST return an `LSP_TIMEOUT` error
- AND provide a recommendation to run `trifecta sync` manually.

### Requirement: Concurrency Shield
The server MUST prevent multiple concurrent tool calls from triggering redundant build operations.

#### Scenario: Concurrent Call Handling
- GIVEN a server currently in the `SYNCING` state
- WHEN a second tool call is received
- THEN the second call SHALL wait for the lock or return a `BUSY/SYNCING` status instead of starting a new build.
