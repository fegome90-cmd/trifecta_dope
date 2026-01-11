## Invariants
- `LSPClient.state` MUST be `READY` after the `initialize` response and `initialized` notification are processed.
- `LSPClient` MUST accept and queue requests while in the `READY` state, even if no diagnostics have been received.
- `LSPClient` MAY log diagnostics when they arrive, but they MUST NOT be a condition for the `READY` state.
