#### Implementation highlights:**
- **LSP dependency:** Pyright requires Node.js (TypeScript-based). For lean/Python-only environments, consider `basedpyright` (pure Python packaging). Document chosen approach in pyproject.toml.
- Subprocess spawn with stdin/stdout pipes (`pyright-langserver --stdio` or `basedpyright-langserver`)
- JSON-RPC Content-Length framing
- State machine: COLD → WARMING (spawn + init) → READY (didOpen + publishDiagnostics) → FAILED (error)
- Warm-up policy: spawn in parallel during AST build, send didOpen for first file
- READY-only gating: requests only when state == READY
- Fallback to AST-only if not READY
- Emit `lsp.spawn`, `lsp.state_change`, `lsp.request`, `lsp.fallback` events
