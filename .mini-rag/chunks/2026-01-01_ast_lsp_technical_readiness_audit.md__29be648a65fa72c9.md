### 3.2 Step 2: Wire Safety Nets (Tests)
Create `tests/integration/test_ast_integration.py`:
- **Test**: Instantiate `LSPManager`, force it to START, verify PID exists.
- **Test**: Parse a `fixture.py` with `ASTParser`, verify specific symbols returned.
- **Fault Injection**: Rename `fixture.py` while LSP is running. Verify system doesn't crash.
