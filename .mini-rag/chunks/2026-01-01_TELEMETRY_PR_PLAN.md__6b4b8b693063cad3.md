### Definition of Done

- [ ] All unit tests pass: `pytest tests/unit/test_telemetry_ast_lsp.py -v`
- [ ] All integration tests pass: `pytest tests/integration/test_lsp_instrumentation.py -v`
- [ ] Synthetic validation passes: `pytest tests/fixtures/synthetic_telemetry.py::test_summary_percentile_validation -v`
- [ ] Coverage >80%: `pytest tests/ --cov=src --cov-report=term-missing | grep TOTAL`
- [ ] No test data logged to real events.jsonl (tests use isolated tmp directories)
- [ ] Concurrent safety validated (3+ threads, no data corruption)

---
