### 2.3 Code Quality & Safety (High)
*   **AST Parser**: `_extract_symbols` is recursive without depth limit. Vulnerable to `RecursionError` on deep code.
*   **LSP Manager**: `stderr=subprocess.DEVNULL` blindly suppresses all startup errors. If `pyright` is missing or crashes, the system fails silently.
*   **Symbol Selector**: Logic is fragile (exact match only). If code drifts by 1 character (e.g., refactor), the selector breaks.

---
