#### Definition of Done (Ticket 1.1)

- [ ] `_write_jsonl()` returns True on success, False on lock skip (for drop tracking)
- [ ] `event()` accepts `**extra_fields` and merges into JSON payload
- [ ] `event()` raises `ValueError` if extra_fields collides with reserved keys
- [ ] `_relpath()` utility converts absolute paths to relative paths
- [ ] All new event fields appear in events.jsonl on write
- [ ] `flush()` calculates AST/LSP/file_read summaries with correct formulas
- [ ] Backward compatibility: old code calling `telemetry.event(cmd, args, result, timing_ms)` still works
- [ ] Unit test: `test_reserved_key_protection` (verify ValueError on collision)
- [ ] Unit test: `test_relpath_normalization` (verify relative path output)
- [ ] Unit test: `test_extra_fields_serialized` (verify bytes_read in event)
- [ ] Unit test: `test_summary_calculations` (verify AST/LSP/file_read in last_run.json)
- [ ] No errors or warnings from linting (mypy, pylint)

---
