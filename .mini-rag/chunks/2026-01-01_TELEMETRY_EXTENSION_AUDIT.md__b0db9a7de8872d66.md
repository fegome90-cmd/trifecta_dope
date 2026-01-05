### F.1 Code Changes

- [ ] **telemetry.py**: Extend `event()` to accept `**extra_fields` (5 lines)
- [ ] **telemetry.py**: Add AST/LSP/file_read summaries to `flush()` (30 lines)
- [ ] **ast_lsp.py**: NEW module with SkeletonMapBuilder, LSPClient, Selector (300+ lines)
  - [ ] Instrumentate `parse_python()` with perf_counter_ns
  - [ ] Instrumentate `send_request()` with perf_counter_ns
  - [ ] Instrumentate `_on_ready()` with cumulative timing
  - [ ] All event() calls use relative paths (via `_relative_path()`)
- [ ] **cli.py**: Add `bytes_read`, `disclosure_mode` fields to ctx.search/get events (10 lines)
- [ ] **file_system.py**: Track `total_bytes_read` per read mode (20 lines)
