### 3.1 Step 1: expose the tools (CLI)
Create `src/infrastructure/cli_ast.py` and wire it into `cli.py`:
- `trifecta ast symbols <query>` -> calls `SymbolSelector`
- `trifecta ast locate <sym_uri>` -> calls `ASTParser`
- `trifecta ast verify` -> runs the 3 safety tests
