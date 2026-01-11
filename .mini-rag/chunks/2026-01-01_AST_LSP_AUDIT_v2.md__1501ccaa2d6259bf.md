### 4. Progressive Disclosure Integration

**Current Implementation:**
- `skeleton`: 25-line excerpt (implemented via `_skeletonize()`)
- `excerpt`: Full function (implemented)
- `raw`: Entire file (implemented)

**V0 Enhancement:**
Add symbol-aware disclosure level selection in `ContextService.search_by_symbol()`:

```python
def search_by_symbol(self, symbol_name: str, kind: str = None) -> SearchResult:
    """AST-aware search: find symbols, return at inferred disclosure level."""

    # Step 1: Resolve symbol → file, line, kind
    symbol_info = self.ast_router.resolve(symbol_name)
    if not symbol_info:
        return SearchResult(hits=[])  # Fail-closed

    # Step 2: Infer disclosure level (heuristic)
    disclosure_level = self._infer_disclosure(
        symbol_name,
        symbol_info["kind"],
        match_exact=True
    )
    # exact → skeleton, ambiguous → excerpt, large → raw

    # Step 3: Retrieve at disclosure level
    chunk = self.get_chunk_at_disclosure(
        symbol_info["file"],
        symbol_info["line"],
        disclosure_level,
        budget_token_est=1500
    )

    return SearchResult(hits=[chunk])
```
