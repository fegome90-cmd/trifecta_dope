#### `src/application/ast_parser.py` (~220 lines)
- **Purpose:** Python AST skeleton extraction with tree-sitter
- **Features:**
  - Content-addressed caching (SHA256 → skeleton)
  - Lazy parser loading (fail-safe if tree-sitter unavailable)
  - Recursive symbol extraction (classes, methods, functions)
  - Privacy-preserving (no absolute paths)
- **Public API:** `SkeletonMapBuilder`, `SymbolInfo`
- **Dependencies:** tree-sitter (lazy), tree-sitter-python (lazy)
