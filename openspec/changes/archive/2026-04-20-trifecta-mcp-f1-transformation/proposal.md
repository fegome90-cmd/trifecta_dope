# Proposal: Trifecta MCP F1 Transformation (Portable)

## Intent
Transform the Trifecta MCP server from a local proxy into a standalone, high-performance "Embedded Engine". The goal is total portability: a single command installation and usage from GitHub (via `uvx` or `pip install`), making all Trifecta structural intelligence available to any agentic workflow in one pass.

## Scope

### In Scope
- **Embedded Architecture**: Move MCP server into the main package (`src/interfaces/mcp/`).
- **Direct Core Integration**: Replace subprocesses and JSON-parsing with direct calls to Trifecta UseCases (Search, Get, Plan, AST, Graph).
- **One-Pass Bootstrap**: Tool `ctx_init` to scaffold and index a repository if context is missing.
- **GitHub Distribution**: Update `pyproject.toml` with console scripts for universal execution (`uvx trifecta-mcp`).
- **Full Capabilities**: Expose AST Analysis, Dependency Graphs, and Strategic Planning as MCP tools.

### Out of Scope
- Integration with external search engines (outside of Trifecta context packs).
- Support for non-Python repositories (Trifecta core remains Python-first for now).

## Capabilities

### New Capabilities
- `mcp-core-engine`: Direct integration of Trifecta logic into MCP protocol.
- `portable-bootstrap`: Zero-config initialization of context packs via MCP.
- `structural-intelligence`: MCP tools for AST and Graph queries.

### Modified Capabilities
- `mcp-search-get`: Refactor existing tools to use real core logic instead of `PackReader` fallback.

## Approach
Re-architect the MCP server as a first-class interface of the Trifecta package. The server will import UseCases from `src/application/`, ensuring that all linter, alias expansion, and AST logic is applied consistently. Distribution will be handled via `project.scripts` in `pyproject.toml`, allowing users to run `uvx --from git+https://github.com/Gentleman-Programming/trifecta_dope trifecta mcp run`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/interfaces/mcp/` | New | New home for the portable MCP server and its handlers. |
| `pyproject.toml` | Modified | Add console scripts and dependencies for MCP server. |
| `tmp_mcp_f1/` | Removed | Original source will be deleted after migration to `src/`. |
| `src/application/` | Modified | Minor refactors to ensure UseCases are import-safe. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Dependency conflicts on install | Low | Use `uvx` to isolate the MCP environment. |
| Performance overhead of AST | Medium | Implement in-memory caching for structural scans. |

## Rollback Plan
Delete `src/interfaces/mcp/` and revert changes to `pyproject.toml`. The original CLI behavior remains untouched as it is decoupled from the MCP interface.

## Success Criteria
- [ ] `uvx trifecta-mcp run --repo .` successfully initializes and starts the server.
- [ ] `ctx_init` tool creates a valid Context Pack in one pass.
- [ ] Agents can query `ast_analyze` and receive structured symbol data.
- [ ] No subprocesses of `uv run` are spawned during tool calls.
