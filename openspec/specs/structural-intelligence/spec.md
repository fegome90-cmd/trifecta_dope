# structural-intelligence Specification

## Purpose
Expose Trifecta's deep structural intelligence (AST and Dependency Graphs) as actionable MCP tools.

## Requirements

### Requirement: AST Symbol Analysis
The system SHALL expose an `ast_analyze` tool that returns structured information about classes, methods, and decorators.

#### Scenario: Analyze File Structure
- GIVEN a Python file path
- WHEN the agent calls `ast_analyze`
- THEN the system SHALL return a JSON map of all top-level symbols and their signatures.

### Requirement: Dependency Graph Query
The system SHALL expose a `graph_query` tool to explore relationships between modules.

#### Scenario: Identify Downstream Impacts
- GIVEN a module name
- WHEN the agent calls `graph_query` with direction="downstream"
- THEN the system SHALL return a list of files that depend on the given module.
