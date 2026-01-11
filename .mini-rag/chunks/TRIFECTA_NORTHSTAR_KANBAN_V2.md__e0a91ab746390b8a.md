### AST/LSP Tools (Separate by Design)
- [x] **AST Symbols M1 (CLI Tool)** `#priority:high` `#phase:3` `#status:verified`
  - **Trace**: [`src/application/symbol_selector.py:78`](file:///Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/src/application/symbol_selector.py#L78), [`src/infrastructure/cli_ast.py`](file:///Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/src/infrastructure/cli_ast.py)
  - **Symbols**: `SymbolResolver` (L78), `SymbolQuery` (L22)
  - **CLI**: `trifecta ast symbols "sym://python/mod/<module>"` (OPERATIONAL)
  - **Tests**: `tests/acceptance/test_ast_symbols_returns_real_symbols.py` (4/4 PASS)
  - **Design Doc**: [`docs/ast-lsp-connect/reevaluation_northstar.md`](file:///Users/felipe_gonzalez/Developer/agent_h/trifecta_dope/docs/ast-lsp-connect/reevaluation_northstar.md)
  - **Status**: ✅ Intentionally separate from Context Pack ("Motor F1" pattern)
