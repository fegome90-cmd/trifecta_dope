#### `src/application/lsp_manager.py` (~240 lines)
- **Purpose:** Pyright LSP headless with state machine
- **Features:**
  - State machine: COLD → WARMING → READY → FAILED
  - Non-blocking warm-up
  - READY-only gating (definition, hover)
  - JSON-RPC 2.0 framing
- **Public API:** `LSPManager`, `LSPState`
- **READY Definition:** initialize ok + didOpen + publishDiagnostics received for URI
