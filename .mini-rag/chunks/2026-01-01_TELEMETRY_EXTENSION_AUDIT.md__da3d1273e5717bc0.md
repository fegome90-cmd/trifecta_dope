### B.4 Definition of "LSP READY"

**NOT:** A custom LSP request (doesn't exist in protocol)

**IS:** One of the following:
1. `initialized` request completed AND `publishDiagnostics` notification received for any file
2. `initialized` request completed AND successful `textDocument/definition` response

**Code trigger points:**
```python
# Condition A: After initialize response
lsp_client.on_notification("textDocument/publishDiagnostics", ...)
# Condition B: After successful definition request
lsp_client.send_request("textDocument/definition", ...)
```

**Telemetry:**
```python
# In DiagnosticsCollector
if (self.initialized and self.first_diagnostics_received) or \
   (self.initialized and self.first_definition_success):
    telemetry.event(
        "lsp.ready",
        {"pyright_binary": "pyright-langserver"},
        {"ready_via": "diagnostics" or "definition"},
        timing_ms=cumulative_from_spawn,
    )
```
