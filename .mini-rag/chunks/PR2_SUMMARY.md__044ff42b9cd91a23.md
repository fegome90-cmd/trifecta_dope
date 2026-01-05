### Run Tests
```bash
# Unit tests for PR#2 components
python -m pytest tests/unit/test_ast_lsp_pr2.py -v

# Integration tests
python -m pytest tests/unit/test_pr2_integration.py -v

# All PR#2 tests
python -m pytest tests/unit/test_ast_lsp_pr2.py tests/unit/test_pr2_integration.py -v

# Expected: 34 passed in 0.17s
```
