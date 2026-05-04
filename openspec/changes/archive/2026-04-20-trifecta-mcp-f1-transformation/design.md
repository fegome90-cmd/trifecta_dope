# Design: Trifecta MCP F1 Transformation (Portable)

## Technical Approach
Convert the MCP server into a native Python entrypoint within the `trifecta` package. The server will act as a **Modular Proxy** that routes JSON-RPC calls directly to `src.application` UseCases, eliminating the need for `uv run` subprocesses. Portability is achieved by leveraging the `pyproject.toml` console scripts and ensuring all core dependencies are standard Python or pinned lightweight libraries.

## Architecture Decisions

### Decision: Embedded Core Execution
**Choice**: The MCP server SHALL import UseCases and execute them in-process.
**Alternatives considered**: Maintaining the `trifecta_runner.py` subprocess bridge.
**Rationale**: In-process execution provides zero-latency tool calls, unified telemetry, and shared memory for caching AST/Graph structures, which is critical for an "F1" level experience.

### Decision: Universal Distribution via `uvx`
**Choice**: Define a `trifecta-mcp` console script in `pyproject.toml`.
**Alternatives considered**: Standalone Docker image or PyInstaller binary.
**Rationale**: `uvx` allows for instant, isolated execution directly from GitHub without manual installation steps, satisfying the "one pass" requirement while remaining lightweight.

## Data Flow
The agent interacts with the MCP Server, which orchestrates the UseCases and returns structured context.

    AI Agent ──(JSON-RPC)──→ MCP Server (src/interfaces/mcp)
                                │
          ┌─────────────────────┴─────────────────────┐
          ▼                     ▼                     ▼
    SearchUseCase         PlanUseCase           AST/Graph Engine
    (Context Retrieval)   (Strategic Planning)  (Structural Intelligence)

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/interfaces/mcp/server.py` | Create | New portable MCP server using direct imports. |
| `src/interfaces/mcp/handlers.py` | Create | Tool-specific logic to map MCP params to UseCase inputs. |
| `pyproject.toml` | Modify | Add `trifecta-mcp` to `[project.scripts]` and add `mcp` extra deps. |
| `src/application/use_cases.py` | Modify | Minor refactors to ensure statelessness for server safety. |
| `tmp_mcp_f1/` | Delete | Clean up the temporary box after migration. |

## Interfaces / Contracts

### New MCP Tool Schema: `ast_analyze`
Returns signatures and docstrings for classes and functions in a file.

### New MCP Tool Schema: `ctx_init`
Automates `create` + `build` sequence for zero-config onboarding.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | UseCase mapping | Test that MCP handlers correctly call UseCases with expected arguments. |
| Integration | Portable Install | Run `uvx` install in a clean temporary directory and verify `ctx_init`. |
| E2E | Agent tool use | Simulate a Claude Code session calling `ast_analyze` and `ctx_search`. |

## Migration / Rollout
1. Implement `src/interfaces/mcp/` in the main repo.
2. Verify with local `python -m src.interfaces.mcp.server`.
3. Add to `pyproject.toml` and release to GitHub.
4. Update `gentle-ai` assets to point to the new `uvx` command.
