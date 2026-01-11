### 2.1 CLI Integration (Critical)
*   **Plan (T3)**: `ast symbols`, `ast locate`, `ast snippet`.
*   **Actual**: `src/infrastructure/cli.py` has ZERO references to `ast_parser` or `lsp_manager`.
*   **Impact**: Agent cannot execute the "Step 2" of the plan (AST navigation).
