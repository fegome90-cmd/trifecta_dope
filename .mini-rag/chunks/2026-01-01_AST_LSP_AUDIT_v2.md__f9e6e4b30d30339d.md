### Success Criteria (PASS/FAIL)

| Metric | PASS Threshold | Phase | Owner |
|--------|---|--------|-------|
| **Skeleton parse latency (p95)** | <100ms per file | T1 | AST |
| **Skeleton cache hit rate** | >85% | T1 | AST |
| **LSP cold start (p50)** | <300ms | T2 | LSP |
| **LSP definition accuracy** | >95% matches correct symbol | T2 | LSP |
| **Symbol resolution success rate** | >90% (fail-closed if unknown) | T3 | Selector |
| **bytes_read_per_task** | <5KB avg (efficiency) | T3 | Disclosure |
| **Fallback rate (LSP → Tree-sitter)** | <5% (should be warm) | T2/T3 | Resilience |
| **Test coverage** | >80% (ast_lsp, lsp_client) | All | QA |
| **Integration test pass rate** | 100% | T3 | Integration |
