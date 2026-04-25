# Delta for unified-intelligence-oracle

## ADDED Requirements

### Requirement: LSP Signal Integration
The system MUST populate `OracleResult.lsp_data` with hover data (type signatures and docstrings) obtained via `LSPClient.request("textDocument/hover", ...)`. This phase is **hover-only** — definition and references are future enhancements. LSP signal activation SHALL be gated by client readiness, query predicate detection, and AST symbol positioning. The system MUST NOT issue speculative LSP requests when AST cannot resolve the symbol position.

#### Scenario: LSP hover for semantic query (EN)
- GIVEN an LSPClient in READY state is injected into the Oracle
- WHEN the query is "what is resolve_segment_ref"
- THEN the system SHALL issue a `textDocument/hover` request for the detected symbol
- AND `metadata.lsp_signal` SHALL be `"lsp_used"`
- AND `lsp_data` SHALL contain hover content with type signature and docstring

#### Scenario: LSP hover for semantic query (ES)
- GIVEN an LSPClient in READY state is injected into the Oracle
- WHEN the query is "que es resolve_segment_ref" or "mostrame resolve_segment_ref"
- THEN the system SHALL issue a `textDocument/hover` request for the detected symbol
- AND `metadata.lsp_signal` SHALL be `"lsp_used"`

### Requirement: LSP Query Predicate Detection
The system MUST detect semantic-resolution predicates in the query and conditionally activate the LSP signal. Queries without detectable semantic predicates SHALL NOT trigger LSP requests.

#### Scenario: Semantic predicate detected (EN)
- GIVEN an LSPClient in READY state
- WHEN the query matches patterns "what is X" or "show me X" where X is a symbol
- THEN the system SHALL extract X as the LSP target
- AND issue a `textDocument/hover` request for X

#### Scenario: Semantic predicate detected (ES)
- GIVEN an LSPClient in READY state
- WHEN the query matches patterns "que es X" or "mostrame X"
- THEN the system SHALL extract X as the LSP target

#### Scenario: Non-semantic query skips LSP
- GIVEN an LSPClient in READY state
- WHEN the query is "how to configure the daemon" or "como configurar el daemon"
- THEN the system SHALL NOT issue any LSP request
- AND `metadata.lsp_signal` SHALL be `"lsp_not_applicable"`

### Requirement: LSP Signal States
The system MUST report a distinct `metadata.lsp_signal` for each LSP outcome. States SHALL be mutually exclusive.

| LSP Signal | Trigger | lsp_data |
|---|---|---|
| `lsp_not_applicable` | Query has no semantic predicate | null |
| `lsp_not_injected` | No LSPClient provided to Oracle | null |
| `lsp_not_ready` | LSPClient.state in {COLD, WARMING, FAILED, CLOSED} | null |
| `lsp_timeout` | LSP request exceeds 20ms per-query budget | null |
| `lsp_error` | LSP returns error response | null |
| `lsp_no_result` | LSP returns null/empty, OR AST cannot resolve symbol position | null |
| `lsp_used` | LSP returns valid hover data | populated |

#### Scenario: Non-semantic query
- GIVEN an LSPClient in READY state
- WHEN the query is "how to configure the daemon"
- THEN `metadata.lsp_signal` SHALL be `"lsp_not_applicable"`
- AND `lsp_data` SHALL be null
- AND no LSP request SHALL be issued

#### Scenario: LSP not injected
- GIVEN no LSPClient is provided to the Oracle
- WHEN a semantic query is executed
- THEN `metadata.lsp_signal` SHALL be `"lsp_not_injected"`
- AND `lsp_data` SHALL be null

#### Scenario: LSP warming
- GIVEN an LSPClient with state WARMING
- WHEN a semantic query is executed
- THEN `metadata.lsp_signal` SHALL be `"lsp_not_ready"`
- AND the Oracle SHALL proceed with PRIME+AST+Graph without regression

#### Scenario: LSP request times out
- GIVEN an LSPClient in READY state
- WHEN an LSP request exceeds 20ms
- THEN `metadata.lsp_signal` SHALL be `"lsp_timeout"`
- AND `lsp_data` SHALL be null
- AND PRIME/AST/Graph results SHALL be untouched

#### Scenario: LSP returns error
- GIVEN an LSPClient in READY state
- WHEN the LSP server returns an error response
- THEN `metadata.lsp_signal` SHALL be `"lsp_error"`

#### Scenario: LSP finds no result
- GIVEN an LSPClient in READY state
- WHEN LSP returns null or empty for the target symbol
- THEN `metadata.lsp_signal` SHALL be `"lsp_no_result"`

#### Scenario: AST cannot resolve symbol position
- GIVEN an LSPClient in READY state and a semantic query
- WHEN AST has no matching symbol for the target
- THEN `metadata.lsp_signal` SHALL be `"lsp_no_result"`
- AND no LSP request SHALL be issued

### Requirement: LSP Latency Budget
The LSP signal MUST complete within 20ms per query. The state check (~1ms) and request+parse (~19ms) SHALL NOT cause total Oracle latency to exceed 65ms.

#### Scenario: LSP within budget
- GIVEN LSP state check takes 1ms and hover request takes 12ms
- WHEN a semantic query is executed
- THEN `metadata.lsp_signal` SHALL be `"lsp_used"`
- AND total Oracle latency SHALL be under 65ms

#### Scenario: LSP exceeds budget
- GIVEN an LSP hover request exceeds 20ms
- WHEN the timeout fires
- THEN the system SHALL discard the LSP result
- AND `metadata.lsp_signal` SHALL be `"lsp_timeout"`

### Requirement: LSP Degradation Contract
When LSP fails or is unavailable, the system SHALL degrade gracefully. Fidelity SHALL downgrade: `full` to `degraded` (AST available) to `fallback` (PRIME only). PRIME, AST, and Graph results MUST NOT regress.

#### Scenario: LSP unavailable degrades fidelity
- GIVEN an LSPClient in FAILED state and AST symbols are available
- WHEN a semantic query is executed
- THEN `fidelity` SHALL be `"degraded"`
- AND `metadata.lsp_signal` SHALL be `"lsp_not_ready"`

#### Scenario: AST-positioned symbol resolution
- GIVEN an LSPClient in READY state and a semantic query for symbol X
- WHEN AST resolves X to file F, line L
- THEN the system SHALL issue `textDocument/hover` with position {F, L}
- AND `lsp_data` SHALL contain hover contents from that exact position

#### Scenario: Multiple AST matches resolved by first match
- GIVEN an LSPClient in READY state and a semantic query for symbol X
- WHEN AST finds X at multiple positions in the same file
- THEN the system SHALL use the first match position for the hover request

### Requirement: LSP Telemetry
Every Oracle invocation MUST emit a `ctx_oracle` telemetry event that includes the `lsp_signal` state.

#### Scenario: Telemetry includes lsp_signal
- GIVEN any Oracle configuration
- WHEN a query is executed
- THEN the `ctx_oracle` telemetry event SHALL include `lsp_signal` in its result payload

## MODIFIED Requirements

### Requirement: Authority-First Fusion
The system MUST prioritize the **PRIME index** as the primary anchor for all intelligence fusion. The GraphStore and LSP are derived, non-authoritative signals that MAY supplement the result for relational and semantic queries respectively but MUST NOT override or contradict PRIME results. LSP data supplements but never replaces PRIME chunks.
(Previously: PRIME was SSOT. GraphStore added as derived signal. Now LSP also added as derived, non-authoritative 4th signal.)

#### Scenario: Unified definition and docs
- GIVEN a running F1 server with a warm PRIME index
- WHEN an agent calls `ctx_oracle` for a class
- THEN the system SHALL return the documentation chunk (PRIME) merged with its structural signature (AST).

#### Scenario: LSP supplements but does not override
- GIVEN a semantic query where PRIME returns doc chunks and LSP returns type signature
- WHEN the Oracle assembles the result
- THEN PRIME chunks SHALL appear in `prime_chunks` and LSP data SHALL appear in `lsp_data`
- AND LSP data SHALL NOT replace or modify PRIME chunk content

### Requirement: Progressive Fidelity Reporting
The system SHALL report the quality of the fused signals based on engine state, including graph signal and LSP signal availability. Fidelity SHALL be `"full"` when LSP returns usable data, `"degraded"` when AST is available without LSP, and `"fallback"` when only PRIME is available.
(Previously: Fidelity reported LSP/AST availability with graph_signal in metadata. Now includes `lsp_signal` metadata and explicit fidelity promotion logic.)

#### Scenario: Fallback indication
- GIVEN a server where LSP is not ready and no AST symbols are available
- WHEN an oracle request is processed
- THEN the response SHALL be marked as `fidelity: fallback`
- AND contain only the PRIME signal

#### Scenario: Full fidelity with LSP
- GIVEN LSP returns usable hover data for a semantic query
- WHEN the oracle returns
- THEN `fidelity` SHALL be `"full"`
- AND `metadata.lsp_signal` SHALL be `"lsp_used"`

#### Scenario: Degraded fidelity with AST only
- GIVEN LSP is unavailable and AST symbols are available
- WHEN the oracle returns
- THEN `fidelity` SHALL be `"degraded"`
- AND `metadata.lsp_signal` SHALL reflect the unavailability reason
