### Definition of Done

- [ ] Tree-sitter Python parser installed and imported successfully
- [ ] SkeletonMapBuilder.parse_python() uses perf_counter_ns for timing
- [ ] LSPClient constructor spawns pyright-langserver subprocess
- [ ] LSPClient.definition() sends textDocument/definition JSON-RPC request
- [ ] LSPClient.definition() timeouts after 500ms (configurable)
- [ ] Selector.resolve_symbol() parses sym:// DSL
- [ ] All event() calls use relative paths (via _relative_path())
- [ ] No sensitive data (API keys, absolute paths) in events
- [ ] Unit test: `test_skeleton_parse_perf_counter_ns` (verify monotonic clock)
- [ ] Unit test: `test_lsp_timeout_fallback` (verify timeout → fallback event)
- [ ] Unit test: `test_selector_resolve_symbol` (basic sym:// parsing)
- [ ] Type hints complete (mypy clean)
- [ ] All imports available (tree-sitter, subprocess, typing)

---
