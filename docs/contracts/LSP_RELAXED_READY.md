# LSP Relaxed READY Contract

## Definition
The **Relaxed READY** contract specifies that the `LSPClient` transitions to the `LSPState.READY` state immediately after a successful `initialize` handshake, **without waiting for `publishDiagnostics` or other server notifications**.

## Rationale
1.  **Latency Reduction**: Waiting for diagnostics can introduce significant delays, especially with large codebases or slow language servers.
2.  **Robustness**: Not all LSP servers guarantee immediate diagnostics upon initialization. Blocking until diagnostics arrive makes the client brittle and dependent on specific server behaviors.
3.  **Use Case Alignment**: Trifecta's primary use cases (symbol search, definition lookup) often require valid file references but do not inherently require a full diagnostic pass to be operational.

## Invariants
- `LSPClient.state` MUST be `READY` after the `initialize` response and `initialized` notification are processed.
- `LSPClient` MUST accept and queue requests while in the `READY` state, even if no diagnostics have been received.
- `LSPClient` MAY log diagnostics when they arrive, but they MUST NOT be a condition for the `READY` state.

## Verification
This contract is verified by:
- `tests/unit/test_lsp_client_strict.py::test_contract_relaxed_ready_immediate`
