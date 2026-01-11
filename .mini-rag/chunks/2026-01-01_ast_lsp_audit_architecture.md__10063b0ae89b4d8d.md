### 3.2 Semantic Rules
1.  **`mod`**: Targets a File Skeleton. `Path` represents the file path (relative to source root, no extension needed if unambiguous, or explicit).
2.  **`type`**: Targets a Top-Level Symbol (Class/Func). `Path` is the File, `Member` (or last part of path?) -- *Clarification*: In this scheme, `Path` locates the file, and the Symbol is purely within the file.
    *   *Refined Rule*: `sym://python/type/<FileStem>/<SymbolName>` relies on `FileStem` finding a file.
    *   To support `sym://python/type/pkg/module/Class`, we use: `sym://python/type/<dotted_or_slashed_path_to_symbol>`.
    *   **Decision**: We split path from symbol.
    *   `sym://python/mod/<path/to/file>`
    *   `sym://python/type/<path/to/file>/<TopLevelSymbol>`
    *   `sym://python/type/<path/to/file>/<Class>#<Method>`
