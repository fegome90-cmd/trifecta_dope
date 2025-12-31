## 2025-12-31 12:46 - LSP/AST positive eval pack
- Added: `minirag-eval/queries/lsp_ast_positive.txt`, `minirag-eval/specs/lsp_ast_positive.md`
- Updated: `minirag-eval/summarize_results.py`, `minirag-eval/queries/all.txt`, `minirag-eval/README.md`
- Ran: `bash minirag-eval/run_bench.sh lsp_ast_positive`
- Summary: core 16/16, negative 5/5, ambiguous 4/5, temporal 5/5, contradictions 4/5, noise 3/5, lsp_ast_positive 9/10
- Note: baseline tests still fail due to missing `validate_agents_constitution` in `src.infrastructure.validators`
