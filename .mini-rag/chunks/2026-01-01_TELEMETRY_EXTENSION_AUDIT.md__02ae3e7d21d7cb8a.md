### Day 2–3: AST/LSP Instrumentation
- [ ] Create **src/infrastructure/ast_lsp.py** with SkeletonMapBuilder + LSPClient + Selector (all with telemetry hooks)
- [ ] Update **cli.py** to emit bytes_read, disclosure_mode
- [ ] Update **file_system.py** to track total_bytes_read
- [ ] 5 unit tests (monotonic, redaction, ready, extra fields, counters)
