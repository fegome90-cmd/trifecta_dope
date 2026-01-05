```python
class DiagnosticsCollector:
    """Collect publishDiagnostics notifications from LSP server."""

    def __init__(self, lsp_client):
        self.diagnostics: dict[str, list] = {}
        self.lsp_client = lsp_client
        # Register handler for incoming notifications
        self.lsp_client.on_notification("textDocument/publishDiagnostics",
                                         self._on_diagnostics)

    def _on_diagnostics(self, params):
        """Handle publishDiagnostics notification."""
        uri = params["uri"]
        diags = params.get("diagnostics", [])
        self.diagnostics[uri] = diags

    def await_diagnostics(self, uri: str, timeout_ms: int = 500) -> list:
        """Wait for diagnostics or timeout."""
        start = time.time()
        while (time.time() - start) * 1000 < timeout_ms:
            if uri in self.diagnostics:
                return self.diagnostics.pop(uri)
            time.sleep(0.01)
        return []  # Timeout → return empty
```

**Timeout & Fallback:**
- If LSP request takes >500ms → fallback to Tree-sitter selector (instant)
- If LSP process dies → return partial results from Tree-sitter
- **User never waits** → worst case 100ms (Tree-sitter parse time)

---
