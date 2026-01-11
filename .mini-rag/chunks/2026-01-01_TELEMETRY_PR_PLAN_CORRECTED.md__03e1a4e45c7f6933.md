#### Definition of Done (Ticket 1.3)

- [ ] All unit tests pass: `pytest tests/unit/test_telemetry_extension.py -v`
- [ ] Coverage >90% for telemetry.py extension code
- [ ] Test: `test_collision_raises_error` (reserved key protection)
- [ ] Test: `test_relpath_inside_workspace` (path normalization)
- [ ] Test: `test_extra_fields_in_event` (serialization)
- [ ] Test: `test_ast_summary` (aggregation)
- [ ] Test: `test_lsp_summary` (aggregation)
- [ ] Test: `test_file_read_summary` (aggregation)
- [ ] Test: `test_monotonic_clock` (timing correctness)
- [ ] Test: `test_concurrent_writes_no_corruption` (concurrency safety)
- [ ] No test data logged to production events.jsonl (tests use tmp_path)
- [ ] Type hints complete (mypy clean)

---
