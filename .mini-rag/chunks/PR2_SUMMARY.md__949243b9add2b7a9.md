#### `LSP_ENABLED` (default: `0`)
- **Purpose:** Enable/disable Pyright LSP warm-up
- **Usage:**
  ```bash
  export LSP_ENABLED=1
  python scripts/demo_pr2.py
  ```
- **Behavior:**
  - If `LSP_ENABLED=1` and pyright available: spawn LSP in background
  - If `LSP_ENABLED=0` or pyright unavailable: AST-only mode (no LSP)
