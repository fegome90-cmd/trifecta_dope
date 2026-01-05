#### `src/application/pr2_context_searcher.py` (~238 lines)
- **Purpose:** Unified façade for AST+Selector+LSP+Telemetry
- **Features:**
  - Progressive disclosure modes: skeleton / excerpt / raw
  - Bytes tracking (file_read_*_bytes_total)
  - Non-blocking LSP warm-up
  - Fallback to AST-only if LSP not READY
- **Public API:** `PR2ContextSearcher`
