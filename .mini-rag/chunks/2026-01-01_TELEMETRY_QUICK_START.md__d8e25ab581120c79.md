## QUICK REFERENCE: Hook Points

| Component | File | Line | What to do |
|-----------|------|------|-----------|
| CLI search | cli.py | 279 | Use perf_counter_ns, add bytes_read, flush on error |
| CLI get | cli.py | 317 | Use perf_counter_ns, add bytes_read + disclosure_mode |
| Telemetry event | telemetry.py | 113 | Accept `**extra_fields`, merge into payload |
| Telemetry flush | telemetry.py | 245 | Add AST/LSP/file_read summaries |
| AST parse | ast_lsp.py | NEW | SkeletonMapBuilder.parse_python() with perf_counter_ns |
| LSP init | ast_lsp.py | NEW | LSPClient.__init__() spawn + telemetry.event("lsp.spawn") |
| LSP definition | ast_lsp.py | NEW | LSPClient.definition() with timeout 500ms + fallback |
| File read | file_system.py | ~ | Track total_bytes_read per mode |

---
