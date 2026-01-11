## 1. Trifecta Philosophy Alignment

The integration MUST adhere to these core principles to avoid "Second System Effect":

1.  **Simplicity & Tool-First**: The Agent is the user. The tool (`trifecta ast`) MUST be "dumb", deterministic, and predictable. No magic "auto-complete" functionality; strictly "fetch this symbol".
2.  **Fail-Closed Security**: If a symbol cannot be resolved explicitly (exact match), fail. It MUST NOT fuzzy-guess. We prefer a `SYMBOL_NOT_FOUND` error over hallucinating a line number.
3.  **Progressive Disclosure (The "Zoom" Metaphor)**:
    *   **L0 (Map)**: `ctx.search` (Files/Concepts)
    *   **L1 (Skeleton)**: `ast symbols` (Class/Func names) -> **Lightweight**
    *   **L2 (Snippet)**: `ast snippet` (Implementation) -> **Medium**
    *   **L3 (Full)**: `ctx.get` (Raw Source) -> **Heavy**
4.  **No "IDE Replacement"**: Usage of LSP is strictly for *read-only navigation* (Go to Definition, Hover), NOT for writing/refactoring. Use standard tools (`sed`, `grep`) for writes.

---
