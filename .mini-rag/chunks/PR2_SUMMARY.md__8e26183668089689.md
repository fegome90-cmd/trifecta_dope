#### `src/application/telemetry_pr2.py` (~230 lines)
- **Purpose:** Telemetry integration bridge for PR#2
- **Features:**
  - ASTTelemetry: ast.parse, cache tracking
  - SelectorTelemetry: selector.resolve
  - FileTelemetry: file.read with bytes tracking
  - LSPTelemetry: lsp.spawn, lsp.state_change, lsp.request, lsp.fallback
- **Public API:** `ASTTelemetry`, `SelectorTelemetry`, `FileTelemetry`, `LSPTelemetry`
