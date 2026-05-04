# Proposal: MCP Intelligence Enrichment & Skill Alignment

## Intent
Align the main Trifecta repository with the best practices discovered during the `tmux_fork` integration. This involves enriching the MCP health reporting, implementing in-memory performance tracking (hit rates), and updating the core Trifecta skill to prioritize high-performance MCP tools over shell commands.

## Scope

### In Scope
- **Server Metrics**: Implement hit/miss counters in `TrifectaF1Server`.
- **Enriched Health**: Update `ctx_health` to report staleness (days), chunk count, and search hit rate.
- **Skill Alignment**: Update `.gemini/skills/trifecta_dope/SKILL.md` with "MCP-First" instructions.
- **PII Unification**: Refactor path redaction into a shared utility in `src/infrastructure/file_system_utils.py`.

### Out of Scope
- Unified Search (Trifecta + Engram) - deferred to a future hito.
- Modification of existing search scoring logic.

## Capabilities

### New Capabilities
- `mcp-performance-tracking`: Real-time monitoring of tool effectiveness within the server process.

### Modified Capabilities
- `mcp-core-engine`: Extended health payload and unified PII safety.
- `trifecta-governance`: Updated skill instructions to enforce MCP tool usage.

## Approach
We will add a telemetry-lite layer to the `TrifectaF1Server` to track usage metrics without persistent overhead. The `ctx_health` tool will be updated to consume these metrics and provide a more descriptive state to the agent. The core skill will be refactored to include a "Power Tools" section for MCP.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/interfaces/mcp/server.py` | Modified | Added metrics tracking and enriched health handler. |
| `src/infrastructure/file_system_utils.py` | Modified | New shared `redact_absolute_paths` utility. |
| `.gemini/skills/trifecta_dope/SKILL.md` | Modified | Updated instructions for AI agents. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Memory leak in metrics | Low | Use simple integer counters reset on restart. |
| Skill confusion | Medium | Clear distinction between CLI (for humans) and MCP (for agents). |

## Rollback Plan
Revert to archived versions of `server.py` and `SKILL.md` using git.

## Success Criteria
- [ ] `ctx_health` returns `stale_days` and `hit_rate`.
- [ ] No duplicated redaction logic in the codebase.
- [ ] Agent successfully identifies and uses `ast_analyze` when asked about file structure.
