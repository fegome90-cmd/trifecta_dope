### Bucket 3: SymbolQuery API Mismatch (7 failures)

```
tests/unit/test_ast_lsp_pr2.py:28: AttributeError: 'Err' object has no attribute 'language'
```

**Root cause**: Tests esperan `SymbolQuery.parse()` retorne `SymbolQuery | None`, pero impl retorna `Result[SymbolQuery, ASTError]`.

**Options**:
- A) Ajustar impl para retornar `SymbolQuery | None` (breaking other code?)
- B) Ajustar tests para usar `.ok()` pattern

**ROI**: 7 failures

---
