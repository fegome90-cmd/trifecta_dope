# Delta for unified-intelligence-oracle

## ADDED Requirements

### Requirement: Graph Signal Routing
The system MUST detect relational predicates in the query string and conditionally activate the GraphStore signal. The graph signal SHALL NOT be consulted for queries without detectable relational predicates.

#### Scenario: Caller predicate detected
- GIVEN a GraphService is injected into the Oracle
- WHEN the query contains "who calls X" or "callers of X"
- THEN the system SHALL resolve X in the graph and return caller nodes
- AND `metadata.graph_signal` SHALL be `"used"`

#### Scenario: Callee predicate detected
- GIVEN a GraphService is injected into the Oracle
- WHEN the query contains "what does X call" or "callees of X"
- THEN the system SHALL resolve X in the graph and return callee nodes
- AND `metadata.graph_signal` SHALL be `"used"`

#### Scenario: No relational predicate
- GIVEN a GraphService is injected into the Oracle
- WHEN the query is "how to configure the daemon"
- THEN the system SHALL NOT consult the graph
- AND `metadata.graph_signal` SHALL be `"no_predicate"`

#### Scenario: Graph not available
- GIVEN no GraphService is injected OR graph DB does not exist
- WHEN the query contains a relational predicate
- THEN the system SHALL proceed with PRIME+AST fallback
- AND `metadata.graph_signal` SHALL be `"unavailable"`

### Requirement: Graph Signal Latency Budget
The graph signal MUST complete within 15ms. If any graph operation exceeds its individual budget, the system SHALL discard the graph result and fall back to PRIME+AST.

#### Scenario: Graph within budget
- GIVEN graph target resolution takes 8ms and traversal takes 4ms
- WHEN the graph signal is activated
- THEN the result SHALL include graph_data with callers/callees
- AND total Oracle latency SHALL be under 65ms

#### Scenario: Graph exceeds budget
- GIVEN graph target resolution exceeds 10ms
- WHEN the graph signal is activated
- THEN the system SHALL discard the graph result
- AND `metadata.graph_signal` SHALL be `"timeout"`
- AND the Oracle SHALL return PRIME+AST results without regression

### Requirement: Graph Staleness Gate
The system MUST NOT use graph data if the graph index is older than 7 days.

#### Scenario: Fresh graph
- GIVEN the graph was indexed 2 days ago
- WHEN a relational predicate is detected
- THEN the system SHALL query the graph normally

#### Scenario: Stale graph
- GIVEN the graph was indexed 10 days ago
- WHEN a relational predicate is detected
- THEN the system SHALL skip the graph signal
- AND `metadata.graph_signal` SHALL be `"stale"`

### Requirement: Graph Result Structure
When the graph signal is used, the OracleResult SHALL include a `graph_data` field containing resolved nodes. The field SHALL be null when the graph is not used.

#### Scenario: Graph data populated
- GIVEN a caller query resolves to 3 callers
- WHEN the Oracle returns
- THEN `graph_data` SHALL contain `{"relation": "callers", "target": "X", "nodes": [<3 GraphNode dicts>], "latency_ms": <int>}`

#### Scenario: Target not found in graph
- GIVEN a caller query for symbol "NonExistent"
- WHEN the graph cannot resolve the target
- THEN `graph_data` SHALL be null
- AND `metadata.graph_signal` SHALL be `"target_not_found"`

## MODIFIED Requirements

### Requirement: Authority-First Fusion
The system MUST prioritize the **PRIME index** as the primary anchor for all intelligence fusion. The GraphStore is a derived, non-authoritative signal that MAY supplement the result for relational queries but MUST NOT override or contradict PRIME results.
(Previously: PRIME was the sole authority anchor. GraphStore added as optional derived signal with explicit non-authority status.)

#### Scenario: Unified definition and docs
- GIVEN a running F1 server with a warm PRIME index
- WHEN an agent calls `ctx_oracle` for a class
- THEN the system SHALL return the documentation chunk (PRIME) merged with its structural signature (AST).

#### Scenario: Graph supplements but does not override
- GIVEN a relational query where PRIME returns doc chunks and the graph returns callers
- WHEN the Oracle assembles the result
- THEN PRIME chunks SHALL appear in `prime_chunks` and graph nodes SHALL appear in `graph_data`
- AND the two signals SHALL NOT be merged or ranked against each other

### Requirement: Progressive Fidelity Reporting
The system SHALL report the quality of the fused signals based on engine state, including graph signal availability.
(Previously: Fidelity reported only LSP/AST availability. Now includes graph_signal status in metadata.)

#### Scenario: Fallback indication
- GIVEN a server where LSP is not ready
- WHEN an oracle request is processed
- THEN the response SHALL be marked as `fidelity: degraded` (or fallback)
- AND contain only the available AST/PRIME signals.

#### Scenario: Full fidelity with graph
- GIVEN LSP is ready AND graph is available AND query has relational predicate
- WHEN the oracle returns
- THEN `fidelity` SHALL be `"full"`
- AND `metadata.graph_signal` SHALL be `"used"`
