# unified-intelligence-oracle Specification

## Purpose
Merge structural intelligence (AST), definition signals (LSP), and authoritative documentation (PRIME) into a single, high-fidelity entry point.

## Requirements

### Requirement: Authority-First Fusion
The system MUST prioritize the **PRIME index** as the primary anchor for all intelligence fusion.

#### Scenario: Unified definition and docs
- GIVEN a running F1 server with a warm PRIME index
- WHEN an agent calls `ctx_oracle` for a class
- THEN the system SHALL return the documentation chunk (PRIME) merged with its structural signature (AST).

### Requirement: Progressive Fidelity Reporting
The system SHALL report the quality of the fused signals based on engine state.

#### Scenario: Fallback indication
- GIVEN a server where LSP is not ready
- WHEN an oracle request is processed
- THEN the response SHALL be marked as `fidelity: degraded` (or fallback)
- AND contain only the available AST/PRIME signals.
