Run: `./minirag-eval/run_bench.sh lsp_ast_positive`
Expected: `minirag-eval/results/lsp_ast_positive.md` created.

**Step 5: Run summary**

Run: `python minirag-eval/summarize_results.py`
Expected: `lsp_ast_positive: 8/10 PASS` (or higher).

**Step 6: Commit**

```bash
git add minirag-eval/queries/lsp_ast_positive.txt \
  minirag-eval/specs/lsp_ast_positive.md \
  minirag-eval/summarize_results.py \
  minirag-eval/README.md \
  minirag-eval/queries/all.txt

git commit -m "test: add lsp/ast positive eval set"
```
