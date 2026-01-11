## EXECUTIVE SUMMARY

**Trifecta is a Python 3.12+ context-calling system** (6,038 LOC across 28 .py files, 784KB in src/) with **existing Progressive Disclosure** (3 modes: skeleton/excerpt/raw) and **fcntl-based locking infrastructure**.

**AST+LSP integration is feasible and minimal**, but:
1. ✅ **No daemon infrastructure exists** → MVP uses on-demand LSP (no persistence). Daemon → Phase 2.
2. ✅ **Progressive Disclosure already works** → Skeleton mode exists and truncates to 25 lines; we plug AST here.
3. ✅ **Session writes unprotected** → Single-writer lock missing; add as prerequisite.

**3 Critical Decisions:**
- Language: **Python only** (v0). TS/JS deferred (no packages installed, zero .ts/.js in repo).
- LSP Strategy: **On-demand headless client** (no persistent daemon). Pyright-langserver via subprocess, live for single request, die.
- Integration Point: **New module `src/infrastructure/ast_lsp.py`** + hook in `ContextService.search()` for symbol-first routing.

**3 Critical Risks & Mitigations:**
- ⚠️ **LSP cold start 2-5s blocks user** → Fallback to Tree-sitter (<50ms) if timeout exceeded.
- ⚠️ **Session append race condition** → Implement fcntl lock on session file (single-writer contract).
- ⚠️ **Diagnostics overflow logs** → Redact file paths and code snippets in telemetry (append-only security).
