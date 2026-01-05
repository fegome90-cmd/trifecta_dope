#### Definition of Done (Ticket 2.3)

- [ ] `Selector.resolve_symbol()` parses sym:// DSL
- [ ] Symbol resolution uses AST skeleton maps (LSP optional)
- [ ] CLI `ctx.search` emits `bytes_read` field
- [ ] CLI `ctx.get` emits `bytes_read` + `disclosure_mode` fields
- [ ] FileSystemAdapter tracks `total_bytes_read` per command
- [ ] All timings use perf_counter_ns
- [ ] All paths relative
- [ ] Unit test: `test_selector_resolve` (sym:// parsing)
- [ ] Integration test: `test_cli_search_telemetry` (bytes_read logged)
- [ ] Integration test: `test_cli_get_telemetry` (disclosure_mode logged)
- [ ] Mypy clean

---
