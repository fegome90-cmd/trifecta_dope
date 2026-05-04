# Design: Trifecta v2.0 Autopilot (Installer & Robust MCP)

## Technical Approach
Implement a multi-layer automation strategy:
1.  **Application Layer**: Create a `BootstrapUseCase` that handles the plumbing (agent wiring, symlinking). It remains agnostic but *searches* for Engram as a value-add.
2.  **Interface Layer (MCP)**: Update `server.py` with a **Lifecycle Manager** that ensures context existence (`Silent Sync`) before accepting RPC calls.
3.  **Strategic Coupling**: The bootstrap command will check for `~/.engram` and, if found, will configure AI agents to use both Trifecta and Engram as a unified intelligence duo.

## Architecture Decisions

### Decision: Agnostic Core / Strategic Installer
**Choice**: The `BootstrapUseCase` SHALL be agnostically designed but include a "Discovery Phase" for Engram.
**Rationale**: Trifecta must remain independent to be portable, but as a strategic product decision, it should "look for its friends" (Engram) during installation to provide a better out-of-the-box experience.

### Decision: MCP Lifecycle Manager
**Choice**: The MCP server SHALL implement a Lifecycle Manager that governs the transition from startup to readiness. It replaces the naive pre-flight build.

**Lifecycle States**:
- `UNINITIALIZED`: Server started, context state unknown.
- `SYNCING`: Active background build/sync operation in progress (locked).
- `READY`: Context Pack exists and is valid.
- `DEGRADED`: Context Pack exists but is stale or has warnings.
- `FAILED`: No Context Pack and auto-build failed, or critical corruption.

**Sync Modes**:
- `auto`: Default. Build if missing, refresh if stale.
- `readonly`: Never write. Fail if context missing.
- `strict`: Build if missing. Fail if stale or invalid (no degraded state allowed).

**Rationale**: Provides transparency and safety for the self-healing process, ensuring the agent is always aware of the context's reliability.

## Data Flow
The user runs bootstrap, which discovers the environment and wires the agents. The MCP server ensures data integrity on every startup.

    User/Agent ──→ [Bootstrap / MCP Server]
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
    [Agnostic Core]          [Discovery Engine]
    (Search/Get/Build)       (Look for Engram/Agents)

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/application/bootstrap_use_case.py` | Create | Implements the cross-platform setup and agent wiring logic. |
| `src/interfaces/mcp/server.py` | Modify | Add `ensure_context_ready()` pre-flight routine. |
| `src/infrastructure/cli.py` | Modify | Add the `bootstrap` command to the Typer app. |
| `src/infrastructure/agent_config.py` | Create | Low-level logic to read/write Claude and OpenCode JSON configs. |

## Interfaces / Contracts

### Strategic Coupling Metadata (MCP `ctx_health`)
Returns `engram_detected: true` if Engram is present on the machine, signaling a "power duo" state to the agent.

## Testing Strategy
Focus on config safety (atomicity) and silent sync reliability.
