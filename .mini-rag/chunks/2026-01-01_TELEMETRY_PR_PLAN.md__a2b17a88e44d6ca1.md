### Definition of Done

- [ ] ctx.search emits bytes_read field in events
- [ ] ctx.get emits bytes_read + disclosure_mode fields in events
- [ ] All timings use perf_counter_ns (monotonic)
- [ ] FileSystemAdapter.total_bytes_read tracks cumulative bytes per command
- [ ] Counters incremented: file_read_skeleton_bytes_total, file_read_excerpt_bytes_total, file_read_raw_bytes_total
- [ ] Unit test: `test_cli_search_emits_bytes_read` (verify field in event)
- [ ] Unit test: `test_cli_get_emits_disclosure_mode` (verify field in event)
- [ ] No breaking changes to CLI args or output format
- [ ] Backward compatible: old commands still work

---
