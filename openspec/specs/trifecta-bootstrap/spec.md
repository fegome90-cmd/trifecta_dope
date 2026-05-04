# trifecta-bootstrap Specification

## Purpose
Automate the installation and configuration of the Trifecta ecosystem on a new environment, focusing on agent wiring and global binary accessibility.

## Requirements

### Requirement: Automated Agent Wiring
The system SHALL provide a mechanism to automatically configure supported AI agents (Claude Code, OpenCode) to use the Trifecta MCP server.

#### Scenario: Configure Claude Code
- GIVEN a MacBook with Claude Code installed but no Trifecta configuration
- WHEN the user runs `trifecta bootstrap --agent claude`
- THEN the system SHALL identify the Claude Code config directory
- AND inject the `uvx trifecta-mcp` server definition into the appropriate configuration file.

#### Scenario: Configure OpenCode
- GIVEN a MacBook with OpenCode installed
- WHEN the user runs `trifecta bootstrap --agent opencode`
- THEN the system SHALL merge the Trifecta MCP definition into `settings.json`.

### Requirement: Global Binary Installation
The bootstrap process SHALL ensure that the `trifecta` binary is accessible in the user's PATH.

#### Scenario: Link Binary to Local Bin
- GIVEN a fresh installation via `uvx`
- WHEN `trifecta bootstrap` is executed
- THEN the system SHALL attempt to symlink the executable to `~/.local/bin/trifecta` if not already present.
