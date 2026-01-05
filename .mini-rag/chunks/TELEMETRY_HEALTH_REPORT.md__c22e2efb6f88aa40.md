## 2. Taxonomy Coverage: 🔄 FIXED

The original report had ~42% events in "Other". New taxonomy classification:

| Category | Commands Included | Count | Share |
|---|---|---|---|
| **Core (Sync/Build)** | `ctx.sync`, `ctx.build`, `stub_regen`, `init` | 897 | 42.4% |
| **PCC (Search/Get)** | `ctx.get` (312), `ctx.search` (94) | 406 | 19.2% |
| **LSP Infra** | `lsp.spawn`, `lsp.fallback`, `lsp.state*`, `lsp.req*` | 351 | 16.6% |
| **Threading/Concurrency** | `thread_*` (load testing artifacts) | 300 | 14.2% |
| **Resolution/Selector** | `selector.resolve` | 64 | 3.0% |
| **File I/O** | `file.read` | 47 | 2.2% |
| **AST / M1** | `ast.symbols`, `ast.parse` | 35 | 1.6% |
| **System/Test** | `test.cmd`, `cli.create` | 14 | 0.7% |

**Verdict**: "Other" reduced to <1%. Taxonomy now accurately ensures visibility into LSP and Threading subsystems.

---
