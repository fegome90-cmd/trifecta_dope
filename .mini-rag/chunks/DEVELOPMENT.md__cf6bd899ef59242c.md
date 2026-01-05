### What Gets Checked

1. **Syntax Validation**
   - YAML/JSON syntax
   - Python AST (detects SyntaxError)
   - Trailing whitespace

2. **Linting** (Ruff - check-only, NO autofix)
   - Unused imports (F401)
   - Unused variables (F841)
   - Syntax errors (E999)

3. **Test Gate**
   - Runs acceptance tests (`-m "not slow"`)
   - Only if Python files in `src/` or `tests/` changed
   - Timeout: 30s
