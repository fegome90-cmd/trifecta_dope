## 6. System Invariants (The "Never" List)

1.  **AST-First**: The system MUST always perform AST resolution before any other operation (LSP).
2.  **Deterministic Failure**: If resolution fails, return `SYMBOL_NOT_FOUND`. **Never** return nearest match.
3.  **Read-Only**: The Dual-Engine NEVER modifies source code.
4.  **Isolation**: An LSP crash **NEVER** crashes the CLI/Agent. Wrap in `try/catch`.
5.  **Fail-Closed**: If `AMBIGUOUS_SYMBOL` occurs, return the error list, do not pick one.

---
