#### `src/application/symbol_selector.py` (~125 lines)
- **Purpose:** sym:// DSL parser and resolver
- **Features:**
  - Syntax: `sym://python/<qualified_name>`
  - Fail-closed ambiguity resolution
  - Returns: file, start_line, end_line
- **Public API:** `SymbolQuery`, `SymbolResolver`, `SymbolResolveResult`
