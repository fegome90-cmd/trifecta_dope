# Proposal: Trifecta v2.0 Autopilot (Installer & Robust MCP)

## Intent
Complete the portable vision of Trifecta by implementing a self-installer (`bootstrap`) and a robust MCP server that handles its own indexing. This ensures that any user can start using Trifecta's structural intelligence on a new MacBook in one pass.

## Scope

### In Scope
- **`trifecta bootstrap`**: CLI command to install binary and configure AI agents (Claude Code, OpenCode).
- **Silent Auto-Sync**: MCP server logic to index a repo on first run if context is missing.
- **Universal Configuration**: Automatic injection of `uvx trifecta-mcp` into agent settings.
- **F1 Suite Exposure**: Full access to AST, Graph, and Plan tools via MCP.

### Out of Scope
- System-level dependency installation (e.g., Python/uv).

## Capabilities

### New Capabilities
- `trifecta-bootstrap`: Automated environment setup and agent wiring.
- `mcp-silent-sync`: Context Pack auto-discovery and creation within the MCP lifecycle.

### Modified Capabilities
- `mcp-core-engine`: Pre-flight checks and direct UseCase integration.

## Approach
Implement `BootstrapUseCase` in the application layer to handle cross-platform setup (Darwin focus). Enhance `src/interfaces/mcp/server.py` with a pre-flight routine that checks for `context_pack.json` and runs `BuildContextPackUseCase` if necessary before starting the RPC loop.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/application/` | New | `bootstrap_use_case.py` implementation. |
| `src/infrastructure/cli.py` | Modified | Add `bootstrap` command. |
| `src/interfaces/mcp/server.py` | Modified | Add silent sync logic. |
| `pyproject.toml` | Modified | Ensure all entrypoints are uvx-ready. |

## Success Criteria
- [ ] `uvx trifecta bootstrap` configures Claude Code without manual file editing.
- [ ] Running `uvx trifecta-mcp` in a fresh repo creates a Context Pack automatically.
- [ ] All 7 F1 tools are responsive and use real repo data.
