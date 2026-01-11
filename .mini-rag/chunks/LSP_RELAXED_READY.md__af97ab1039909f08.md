## Definition
The **Relaxed READY** contract specifies that the `LSPClient` transitions to the `LSPState.READY` state immediately after a successful `initialize` handshake, **without waiting for `publishDiagnostics` or other server notifications**.
