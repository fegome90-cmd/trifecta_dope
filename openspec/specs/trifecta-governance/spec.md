# trifecta-governance Specification

## Purpose
Enforce best practices and "MCP-First" behavior for AI agents interacting with the Trifecta ecosystem.

## Requirements

### Requirement: Agent Onboarding Contract
The system MUST provide a mandatory onboarding contract for all agents via the `skill.md`, `prime_*.md`, `agent_*.md`, and `session_*.md` files.

#### Scenario: Onboarding Verification
- GIVEN a new agent session
- WHEN the agent enters the workspace
- THEN it SHALL read the 4 mandatory files before executing commands.

### Requirement: MCP-First Tool Prioritization
The `skill.md` SHALL explicitly instruct agents to prioritize MCP tools (e.g., `ctx_search`, `ctx_oracle`) over raw shell commands (`run_shell_command`).

#### Scenario: Tool Choice
- GIVEN an agent tasked with code investigation
- WHEN searching for definitions
- THEN it SHALL use `ast_analyze` or `ctx_oracle` via MCP.
