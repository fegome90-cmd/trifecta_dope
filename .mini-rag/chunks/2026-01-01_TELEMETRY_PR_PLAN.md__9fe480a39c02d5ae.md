### Definition of Done

- [ ] `event()` accepts `**extra_fields` and merges into JSON payload
- [ ] All new event fields appear in events.jsonl on write
- [ ] `flush()` calculates and outputs AST/LSP/file_read summaries
- [ ] Backward compatibility: old code calling `telemetry.event(cmd, args, result, timing_ms)` still works
- [ ] Unit test: `test_telemetry_extra_fields_serialized` (verify bytes_read in event)
- [ ] Unit test: `test_telemetry_summary_calculations` (verify AST/LSP/file_read in last_run.json)
- [ ] No errors or warnings from linting (mypy, pylint)

---
