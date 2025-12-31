### Task 3: Wire the new module into bench tooling

**Files:**
- Modify: `minirag-eval/summarize_results.py`
- Modify: `minirag-eval/README.md`
- Modify: `minirag-eval/queries/all.txt`

**Step 1: Extend `summarize_results.py`**

```python
results["lsp_ast_positive"] = parse_results(base / "lsp_ast_positive.md")

query_sets["lsp_ast_positive"] = [
    "implementacion de ast tree-sitter",
    "ast parser tree-sitter skeletonizer",
    "que extraer del AST",
    "implementacion de lsp symbols hover diagnostics",
    "workspace symbols lsp search",
    "lsp document symbols structure",
    "lsp go to definition hover",
    "lsp diagnostics hot files",
    "fase 3 ast lsp ide grade fluidity",
    "ast lsp hot files roadmap roi",
]

def lsp_ast_pass(query: str) -> bool:
    payload = results["lsp_ast_positive"].get(query, {})
    return any(
        s.endswith("2025-12-29-trifecta-context-loading.md")
        or s.endswith("research_roi_matrix.md")
        or s.endswith("agent_factory.md")
        or "all_bridges.md" in s
        for s in top_sources(payload)
    )

matchers["lsp_ast_positive"] = lsp_ast_pass
```

**Step 2: Update `minirag-eval/README.md`**

Add `lsp_ast_positive` to the module list and run examples.

**Step 3: Update `minirag-eval/queries/all.txt`**

Append the new 10 queries to the end of the file.

**Step 4: Run the module bench**
