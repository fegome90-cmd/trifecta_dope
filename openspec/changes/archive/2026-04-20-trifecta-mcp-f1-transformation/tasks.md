# Tasks: Trifecta MCP F1 Transformation (Portable)

## Phase 1: Foundation & Packaging
- [ ] 1.1 Create `src/interfaces/mcp/__init__.py` to expose the MCP interface.
- [ ] 1.2 Modify `pyproject.toml` to add `mcp` extra dependency and `trifecta-mcp` console script.
- [ ] 1.3 Refactor `src/application/use_cases.py` to ensure `BuildContextPackUseCase` and `SearchUseCase` are stateless and import-safe.

## Phase 2: Core MCP Server Implementation
- [ ] 2.1 Create `src/interfaces/mcp/server.py` with JSON-RPC 2.0 loop and stdio transport.
- [ ] 2.2 Create `src/interfaces/mcp/handlers.py` to map MCP tools to real UseCases.
- [ ] 2.3 Implement `ctx_init` tool handler to automate repo scaffolding and indexing.
- [ ] 2.4 Implement `ast_analyze` tool using the internal AST engine.

## Phase 3: Intelligence & Telemetry
- [ ] 3.1 Implement `graph_query` tool for module relationships.
- [ ] 3.2 Integrate Telemetry and PCC Metrics into tool responses.
- [ ] 3.3 Add global PII sanitization to all MCP outputs.

## Phase 4: Verification & Cleanup
- [ ] 4.1 Write integration tests for `uvx` installation flow.
- [ ] 4.2 Verify `ctx_init` happy path in a clean temp directory.
- [ ] 4.3 Delete `tmp_mcp_f1/` and legacy bridge code.
