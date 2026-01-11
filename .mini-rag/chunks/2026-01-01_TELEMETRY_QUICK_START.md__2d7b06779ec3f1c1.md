### 📦 TICKET 2: AST+LSP Module (16 hours)
**File:** `src/infrastructure/ast_lsp.py` (NEW)

**Classes to implement:**
1. `SkeletonMapBuilder` (300 lines)
   - `parse_python(code, file_path)` → SkeletonMap
   - Uses tree-sitter for parsing
   - Emits `ast.parse` event with monotonic timing

2. `LSPClient` (200 lines)
   - `__init__(telemetry, pyright_binary)`
   - `initialize(workspace_path)`
   - `definition(file_path, line, col)` → response (or timeout)
   - Emits `lsp.spawn`, `lsp.initialize`, `lsp.definition`, `lsp.timeout` events

3. `Selector` (100 lines)
   - `resolve_symbol(symbol_query)` → {file, line, kind}
   - Parses `sym://python/module/Name`
   - Emits `selector.resolve` event

**Dependencies to install:**
```bash
pip install tree-sitter tree-sitter-python
```

**Tests:**
- `test_skeleton_parse_perf_counter_ns`
- `test_lsp_timeout_fallback`
- `test_selector_resolve_symbol`

**Verify:**
```bash
python -m pytest tests/unit/test_ast_lsp.py -v
python -c "from src.infrastructure.ast_lsp import SkeletonMapBuilder, LSPClient, Selector; print('✓ Imports OK')"
```
